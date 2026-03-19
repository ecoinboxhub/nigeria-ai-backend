import logging
from supabase import create_client, Client
from app.core.config import settings

logger = logging.getLogger(__name__)

def get_supabase_client() -> Client:
    """
    Initializes and returns a Supabase client.
    """
    if not settings.supabase_url or not settings.supabase_key:
        logger.error("Supabase credentials missing in settings.")
        raise ValueError("Supabase configuration is incomplete.")
    
    try:
        return create_client(settings.supabase_url, settings.supabase_key)
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise

def get_supabase_admin_client() -> Client:
    """
    Returns a client with the service role key for admin operations.
    """
    if not settings.supabase_url or not settings.supabase_service_role_key:
        logger.error("Supabase service role key missing.")
        raise ValueError("Supabase admin configuration is incomplete.")
    
    return create_client(settings.supabase_url, settings.supabase_service_role_key)

# Singleton-ish client for reuse (Uses Service Role Key for backend admin access)
try:
    if settings.supabase_url and settings.supabase_service_role_key:
        supabase: Client = create_client(settings.supabase_url, settings.supabase_service_role_key)
    else:
        supabase = None
except Exception as e:
    logger.warning(f"Could not initialize global Supabase client: {e}")
    supabase = None
