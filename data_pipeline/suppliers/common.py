import random
import time
from dataclasses import dataclass

import requests
from bs4 import BeautifulSoup

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
    "Mozilla/5.0 (X11; Linux x86_64)",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
]


@dataclass
class ScrapeResult:
    url: str
    html: str


def fetch_with_retries(url: str, retries: int = 4, timeout: int = 20) -> ScrapeResult:
    backoff = 1
    for attempt in range(retries):
        try:
            headers = {"User-Agent": random.choice(USER_AGENTS)}
            resp = requests.get(url, headers=headers, timeout=timeout)
            if resp.status_code in (429, 500, 502, 503, 504):
                raise requests.HTTPError(f"temporary status {resp.status_code}")
            resp.raise_for_status()
            return ScrapeResult(url=url, html=resp.text)
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(backoff)
            backoff *= 2


def parse_html(html: str) -> BeautifulSoup:
    return BeautifulSoup(html, "html.parser")
