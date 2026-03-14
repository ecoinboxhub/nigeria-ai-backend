import json
import os
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx


ROOT = Path(__file__).resolve().parents[2]
HOST = "127.0.0.1"
PORT = int(os.getenv("API_TEST_PORT", "8000"))
BASE_URL = f"http://{HOST}:{PORT}"
REPORT_PATH = ROOT / "artifacts" / "reports" / "api_validation_report.json"
PAYLOAD_DIR = ROOT / "backend" / "scripts" / "payloads"
API_KEY = os.getenv("API_KEY", "change-me")
USE_EXISTING_API = os.getenv("USE_EXISTING_API", "true").lower() == "true"


def _record(checks: list[dict], name: str, method: str, path: str, status_code: int | None, ok: bool, latency_ms: float, response: str = "", error: str = "") -> None:
    checks.append(
        {
            "name": name,
            "method": method,
            "path": path,
            "status_code": status_code,
            "ok": ok,
            "latency_ms": round(latency_ms, 2),
            "response_preview": response[:500],
            "error": error,
        }
    )


def _wait_for_api(client: httpx.Client, timeout_sec: int = 180) -> bool:
    print(f"Waiting for API at {BASE_URL}...")
    start = time.time()
    while time.time() - start < timeout_sec:
        try:
            # Try both 127.0.0.1 and localhost
            for host in ["127.0.0.1", "localhost"]:
                try:
                    r = client.get(f"http://{host}:{PORT}/api/v1/health", timeout=2)
                    if r.status_code == 200:
                        print(f"API is ready at {host}:{PORT}")
                        return True
                except Exception:
                    continue
        except Exception:
            pass
        time.sleep(2)
    return False


def main() -> int:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    PAYLOAD_DIR.mkdir(parents=True, exist_ok=True)

    proc = None
    if not USE_EXISTING_API:
        proc = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "uvicorn",
                "app.main:app",
                "--app-dir",
                "backend",
                "--host",
                HOST,
                "--port",
                str(PORT),
            ],
            cwd=str(ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

    checks: list[dict] = []
    started_at = datetime.now(UTC).isoformat()

    try:
        with httpx.Client(timeout=20.0) as client:
            if not _wait_for_api(client):
                startup_error = "API did not become ready in time"
                if proc is not None and proc.poll() is not None:
                    stderr_out = (proc.stderr.read() or "").strip() if proc.stderr else ""
                    stdout_out = (proc.stdout.read() or "").strip() if proc.stdout else ""
                    details = "\n".join([x for x in [stderr_out, stdout_out] if x]).strip()
                    if details:
                        startup_error = f"{startup_error}. Uvicorn output:\n{details[-2000:]}"
                _record(checks, "api_startup", "GET", "/api/v1/health", None, False, 0.0, error=startup_error)
                report = {
                    "started_at": started_at,
                    "finished_at": datetime.now(UTC).isoformat(),
                    "base_url": BASE_URL,
                    "summary": {"total": len(checks), "passed": 0, "failed": len(checks)},
                    "checks": checks,
                }
                REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
                return 1

            def run_check(name: str, method: str, path: str, expected_status: int = 200, headers: dict | None = None, json_body: dict | None = None) -> httpx.Response | None:
                url = f"{BASE_URL}{path}"
                t0 = time.perf_counter()
                try:
                    resp = client.request(method=method, url=url, headers=headers, json=json_body)
                    dt = (time.perf_counter() - t0) * 1000
                    ok = resp.status_code == expected_status
                    _record(checks, name, method, path, resp.status_code, ok, dt, response=resp.text)
                    return resp
                except Exception as exc:
                    dt = (time.perf_counter() - t0) * 1000
                    _record(checks, name, method, path, None, False, dt, error=str(exc))
                    return None

            health = run_check("health", "GET", "/api/v1/health")

            def load_payload(file_name: str) -> dict:
                payload_file = PAYLOAD_DIR / file_name
                if not payload_file.exists():
                    return {}
                return json.loads(payload_file.read_text(encoding="utf-8"))

            token_resp = run_check(
                "integration_token",
                "POST",
                "/api/v1/integration/token",
                headers={"X-API-Key": API_KEY},
                json_body=load_payload("integration_token.json"),
            )

            token = ""
            refresh = ""
            if token_resp is not None and token_resp.status_code == 200:
                token = token_resp.json().get("access_token", "")
                refresh = token_resp.json().get("refresh_token", "")

            auth_headers = {"Authorization": f"Bearer {token}"} if token else {}

            refresh_payload = load_payload("integration_refresh.json")
            if refresh:
                refresh_payload["refresh_token"] = refresh
            run_check(
                "integration_refresh",
                "POST",
                "/api/v1/integration/refresh",
                json_body=refresh_payload,
            )
            run_check("integration_module_status", "GET", "/api/v1/integration/module-status", headers=auth_headers)
            run_check("integration_endpoints", "GET", "/api/v1/integration/endpoints", headers=auth_headers)

            run_check(
                "project_tracker_predict_delay",
                "POST",
                "/api/v1/project-tracker/predict-delay",
                headers=auth_headers,
                json_body=load_payload("project_tracker_predict_delay.json"),
            )
            run_check(
                "procurement_supplier_intelligence",
                "POST",
                "/api/v1/procurement/supplier-intelligence",
                headers=auth_headers,
                json_body=load_payload("procurement_supplier_intelligence.json"),
            )
            run_check(
                "safety_analyze_log",
                "POST",
                "/api/v1/safety/analyze-log",
                headers=auth_headers,
                json_body=load_payload("safety_analyze_log.json"),
            )
            run_check(
                "document_analyzer_review",
                "POST",
                "/api/v1/document-analyzer/review",
                headers=auth_headers,
                json_body=load_payload("document_analyzer_review.json"),
            )
            run_check(
                "cost_estimator_estimate",
                "POST",
                "/api/v1/cost-estimator/estimate",
                headers=auth_headers,
                json_body=load_payload("cost_estimator_estimate.json"),
            )
            run_check(
                "workforce_optimize",
                "POST",
                "/api/v1/workforce/optimize",
                headers=auth_headers,
                json_body=load_payload("workforce_optimize.json"),
            )
            run_check(
                "maintenance_predict",
                "POST",
                "/api/v1/maintenance/predict",
                headers=auth_headers,
                json_body=load_payload("maintenance_predict.json"),
            )
            run_check(
                "progress_visualizer_analyze",
                "POST",
                "/api/v1/progress-visualizer/analyze",
                headers=auth_headers,
                json_body=load_payload("progress_visualizer_analyze.json"),
            )
            run_check(
                "tender_analyzer_analyze",
                "POST",
                "/api/v1/tender-analyzer/analyze",
                headers=auth_headers,
                json_body=load_payload("tender_analyzer_analyze.json"),
            )

        passed = sum(1 for c in checks if c["ok"])
        failed = len(checks) - passed
        report = {
            "started_at": started_at,
            "finished_at": datetime.now(UTC).isoformat(),
            "base_url": BASE_URL,
            "summary": {"total": len(checks), "passed": passed, "failed": failed},
            "checks": checks,
        }
        REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
        print(str(REPORT_PATH))
        print(json.dumps(report["summary"]))
        return 0 if failed == 0 else 1

    finally:
        if proc and proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                proc.kill()


if __name__ == "__main__":
    raise SystemExit(main())
