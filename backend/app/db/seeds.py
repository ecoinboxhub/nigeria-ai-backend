import logging
from app.db.supabase import get_supabase_admin_client

logger = logging.getLogger(__name__)

MATERIALS_SEED = [
    {"name": "Dangote Cement", "category": "Cement & Concrete", "sub_category": "Cement", "unit": "50kg Bag"},
    {"name": "Lafarge Cement", "category": "Cement & Concrete", "sub_category": "Cement", "unit": "50kg Bag"},
    {"name": "BUA Cement", "category": "Cement & Concrete", "sub_category": "Cement", "unit": "50kg Bag"},
    {"name": "Eagle Cement", "category": "Cement & Concrete", "sub_category": "Cement", "unit": "50kg Bag"},
    {"name": "Ready-mix concrete", "category": "Cement & Concrete", "sub_category": "Concrete", "unit": "per m3"},
    {"name": "Iron rod (6mm)", "category": "Steel & Reinforcement", "sub_category": "Rebars", "unit": "per Ton"},
    {"name": "Iron rod (8mm)", "category": "Steel & Reinforcement", "sub_category": "Rebars", "unit": "per Ton"},
    {"name": "Iron rod (10mm)", "category": "Steel & Reinforcement", "sub_category": "Rebars", "unit": "per Ton"},
    {"name": "Iron rod (12mm)", "category": "Steel & Reinforcement", "sub_category": "Rebars", "unit": "per Ton"},
    {"name": "Iron rod (16mm)", "category": "Steel & Reinforcement", "sub_category": "Rebars", "unit": "per Ton"},
    {"name": "Iron rod (20mm)", "category": "Steel & Reinforcement", "sub_category": "Rebars", "unit": "per Ton"},
    {"name": "Granite (1/2 inch)", "category": "Aggregates & Sand", "sub_category": "Granite", "unit": "20 Tons Truck"},
    {"name": "Granite (3/4 inch)", "category": "Aggregates & Sand", "sub_category": "Granite", "unit": "20 Tons Truck"},
    {"name": "Sharp sand", "category": "Aggregates & Sand", "sub_category": "Sand", "unit": "20 Tons Truck"},
    {"name": "Aluminum roofing sheets", "category": "Roofing Materials", "sub_category": "Sheets", "unit": "per Sqm"},
    {"name": "Ceramic tiles", "category": "Flooring & Finishing", "sub_category": "Tiles", "unit": "per Box"},
    {"name": "Emulsion paint", "category": "Paints & Coatings", "sub_category": "Paint", "unit": "20L Bucket"},
    {"name": "PVC pipes", "category": "Plumbing & Sanitary", "sub_category": "Pipes", "unit": "Length"},
    {"name": "Armoured cables", "category": "Electrical Materials", "sub_category": "Cables", "unit": "per Roll"},
    {"name": "Asphalt", "category": "Road Construction Materials", "sub_category": "Bitumen", "unit": "per Ton"},
]

PROJECTS_SEED = [
    {
        "name": "Eko Atlantic Phase 2",
        "location": "Lagos",
        "status": "active",
        "budget_ngn": 1500000000.0,
        "progress_pct": 35.5
    },
    {
        "name": "Abuja Central Business District Ext",
        "location": "Abuja",
        "status": "active",
        "budget_ngn": 850000000.0,
        "progress_pct": 12.0
    },
    {
        "name": "Enugu Specialized Hospital",
        "location": "Enugu",
        "status": "on_hold",
        "budget_ngn": 420000000.0,
        "progress_pct": 85.0
    },
    {
        "name": "Lekki-Epe Expressway Retrofit",
        "location": "Lagos",
        "status": "active",
        "budget_ngn": 2100000000.0,
        "progress_pct": 5.0
    }
]

def seed_materials():
    client = get_supabase_admin_client()
    if not client: 
        logger.error("Supabase admin client not available for seeding.")
        return
    
    logger.info(f"Seeding {len(MATERIALS_SEED)} priority materials...")
    try:
        res = client.table("materials").upsert(MATERIALS_SEED, on_conflict="name").execute()
        logger.info(f"Successfully seeded materials.")
    except Exception as e:
        logger.error(f"Material seeding failed: {e}")

def seed_projects():
    client = get_supabase_admin_client()
    if not client: return
    
    logger.info(f"Seeding {len(PROJECTS_SEED)} sample projects...")
    for project in PROJECTS_SEED:
        try:
            # Check if project exists by name first (since no unique constraint)
            existing = client.table("projects").select("id").eq("name", project["name"]).execute()
            if not existing.data:
                client.table("projects").insert(project).execute()
                logger.info(f"Seeded project: {project['name']}")
            else:
                logger.info(f"Project already exists: {project['name']}")
        except Exception as e:
            logger.error(f"Failed to seed project {project['name']}: {e}")

if __name__ == "__main__":
    seed_materials()
    seed_projects()
