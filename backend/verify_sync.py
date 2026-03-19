import logging
import json
from app.db.supabase import supabase
from app.services.weather_service import weather_service
from app.services.scraper_engine import price_engine

logger = logging.getLogger(__name__)

def verify_and_sync():
    print("--- 1. Verifying Materials Table ---")
    try:
        res = supabase.table("materials").select("id, name").limit(5).execute()
        print(f"Found {len(res.data)} materials in Supabase.")
        for item in res.data:
            print(f"- {item['name']}")
    except Exception as e:
        print(f"Materials verification failed: {e}")

    print("\n--- 2. Triggering Weather Sync ---")
    try:
        weather_data = weather_service.fetch_all_configured_cities()
        print(f"Synced weather for {len(weather_data)} cities.")
    except Exception as e:
        print(f"Weather sync failed: {e}")

    print("\n--- 3. Triggering Sample Price Sync ---")
    try:
        sample_materials = ["Dangote Cement", "Iron rod (12mm)"]
        price_engine.update_all_materials(sample_materials)
        print(f"Price sync triggered for {sample_materials}.")
    except Exception as e:
        print(f"Price sync failed: {e}")

if __name__ == "__main__":
    verify_and_sync()
