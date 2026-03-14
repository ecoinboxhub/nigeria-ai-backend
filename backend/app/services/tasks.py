import subprocess

from app.services.celery_app import celery_app


@celery_app.task
def run_supplier_scraping() -> dict:
    commands = [
        ["python", "data_pipeline/suppliers/scrape_jiji.py"],
        ["python", "data_pipeline/suppliers/scrape_dealers.py"],
        ["python", "data_pipeline/suppliers/clean_prices.py"],
    ]
    results = []
    for cmd in commands:
        p = subprocess.run(cmd, capture_output=True, text=True)
        results.append({"cmd": " ".join(cmd), "code": p.returncode, "stderr": p.stderr[-300:]})
    return {"steps": results}
