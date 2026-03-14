from apscheduler.schedulers.blocking import BlockingScheduler

from data_pipeline.suppliers.clean_prices import main as clean_prices
from data_pipeline.suppliers.scrape_dealers import main as scrape_dealers
from data_pipeline.suppliers.scrape_jiji import main as scrape_jiji


def run_once() -> None:
    scrape_jiji()
    scrape_dealers()
    clean_prices()


def main() -> None:
    scheduler = BlockingScheduler(timezone="UTC")
    scheduler.add_job(run_once, "interval", hours=6, id="supplier_scrape", replace_existing=True)
    run_once()
    scheduler.start()


if __name__ == "__main__":
    main()
