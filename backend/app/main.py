import logging
from app.core.config import settings
from app.core.logging import configure_logging

# Initialize environment and logging immediately
configure_logging()

logger = logging.getLogger(__name__)

from contextlib import asynccontextmanager
from time import perf_counter

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

from app.api.v1.router import api_router
from app.core.security import decode_raw_token
from app.db.models import AuditLog
from app.db.session import Base, SessionLocal, engine
from app.services.metrics import REQUEST_COUNT, REQUEST_LATENCY
from app.services.metrics import metrics as metrics_handler
from app.services.scheduler import start_scheduler, stop_scheduler
from app.utils.security_utils import RequestLoggingMiddleware

limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        logger.error(f"Database initialization failed during startup: {e}")
        # Allow API startup when DB is temporarily unavailable.
        pass
    start_scheduler()
    yield
    stop_scheduler()


app = FastAPI(title=settings.app_name, version="0.2.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(RequestLoggingMiddleware)

if settings.production_domain:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.production_domain],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def request_metrics_and_audit(request: Request, call_next):
    start = perf_counter()
    response = await call_next(request)
    elapsed = perf_counter() - start

    REQUEST_COUNT.labels(request.method, request.url.path, str(response.status_code)).inc()
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(elapsed)

    db = SessionLocal()
    try:
        user_id = None
        auth = request.headers.get("authorization", "")
        if auth.startswith("Bearer "):
            token = auth.split(" ")[1]
            try:
                payload = decode_raw_token(token)
                user_id = payload.get("sub")
            except Exception:
                user_id = "invalid_token"
        db.add(
            AuditLog(
                user_id=str(user_id) if user_id else None,
                endpoint=request.url.path,
                method=request.method,
                ip_address=request.client.host if request.client else None,
                response_status=response.status_code,
            )
        )
        db.commit()
    except Exception as e:
        logger.warning(f"Failed to record audit log: {e}")
        db.rollback()
    finally:
        db.close()

    return response


app.include_router(api_router, prefix=settings.api_prefix)


@app.get("/health")
def root_health():
    return {"status": "ok"}


@app.get("/metrics")
def root_metrics():
    return metrics_handler()
