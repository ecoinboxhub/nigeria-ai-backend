import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup
from app.db.supabase import supabase

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """
    Abstract Base Class for all marketplace scrapers.
    """
    def __init__(self, source_name: str, base_url: str):
        self.source_name = source_name
        self.base_url = base_url
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    @abstractmethod
    def scrape_material(self, material_name: str) -> dict[str, Any] | None:
        """
        Search for a material and return the best price point found.
        """
        pass

    def _persist_price(self, material_name: str, price: float, url: str) -> bool:
        """
        Saves the price point to Supabase.
        """
        if not supabase: return False
        try:
            # 1. Get or Create Material ID
            mat_res = supabase.table("materials").select("id").eq("name", material_name).execute()
            if not mat_res.data:
                # Fallback: create material if it doesn't exist
                mat_res = supabase.table("materials").insert({
                    "name": material_name, 
                    "category": "Miscellaneous", 
                    "unit": "unit"
                }).execute()
            
            material_id = mat_res.data[0]["id"]

            # 2. Insert Price Point
            supabase.table("price_points").insert({
                "material_id": material_id,
                "price": price,
                "source_name": self.source_name,
                "source_url": url,
                "captured_at": datetime.now(UTC).isoformat()
            }).execute()
            return True
        except Exception as e:
            logger.error(f"[{self.source_name}] Failed to persist price for {material_name}: {e}")
            return False

class CutstructScraper(BaseScraper):
    def __init__(self):
        super().__init__("Cutstruct", "https://cutstruct.com/marketplace")

    def scrape_material(self, material_name: str) -> dict[str, Any] | None:
        try:
            # Cutstruct uses a structured marketplace. We'll simulate a search.
            search_url = f"{self.base_url}?search={material_name.replace(' ', '+')}"
            with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(search_url)
                if resp.status_code != 200: return None
                soup = BeautifulSoup(resp.text, "html.parser")
                # Attempt to find prices in product cards
                prices = soup.find_all(text=lambda t: '₦' in t)
                if prices:
                    # Return the first valid price
                    p_str = prices[0].replace('₦', '').replace(',', '').strip()
                    return {"price": float(p_str), "url": search_url}
            return None
        except Exception as e:
            logger.error(f"Cutstruct scraper failed for {material_name}: {e}")
            return None

class NigerianPriceScraper(BaseScraper):
    def __init__(self):
        super().__init__("NigerianPrice", "https://nigerianprice.com")

    def scrape_material(self, material_name: str) -> dict[str, Any] | None:
        try:
            # This site often has dedicated pages for materials like 'cement-price'
            slug = material_name.lower().replace(' ', '-')
            search_url = f"{self.base_url}/{slug}-price-in-nigeria/"
            with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(search_url)
                if resp.status_code != 200:
                    # Try a generic search if the slug fails
                    search_url = f"{self.base_url}/?s={material_name.replace(' ', '+')}"
                    resp = client.get(search_url)
                
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "html.parser")
                    # Look for table data or bold text containing prices
                    prices = soup.find_all(text=lambda t: '₦' in t or 'price' in t.lower())
                    if prices:
                        # Extract first numeric value after Naira sign
                        import re
                        match = re.search(r'₦\s?([\d,]+)', str(prices[0]))
                        if match:
                            val = match.group(1).replace(',', '')
                            return {"price": float(val), "url": search_url}
            return None
        except Exception as e:
            logger.error(f"NigerianPrice scraper failed for {material_name}: {e}")
            return None

class BuildersMartScraper(BaseScraper):
    def __init__(self):
        super().__init__("BuildersMart", "https://buildersmart.ng")

    def scrape_material(self, material_name: str) -> dict[str, Any] | None:
        try:
            search_url = f"{self.base_url}/search?q={material_name.replace(' ', '+')}"
            with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(search_url)
                if resp.status_code != 200: return None
                soup = BeautifulSoup(resp.text, "html.parser")
                # Look for price classes like 'price' or 'money'
                price_tags = soup.select(".price, .money, .product-price")
                for tag in price_tags:
                    p_str = tag.text.replace('₦', '').replace(',', '').strip()
                    try:
                        return {"price": float(p_str), "url": search_url}
                    except ValueError: continue
            return None
        except Exception as e:
            logger.error(f"BuildersMart scraper failed for {material_name}: {e}")
            return None

class JijiScraper(BaseScraper):
    def __init__(self):
        super().__init__("Jiji.ng", "https://jiji.ng")

    def scrape_material(self, material_name: str) -> dict[str, Any] | None:
        try:
            search_url = f"{self.base_url}/building-materials?query={material_name.replace(' ', '%20')}"
            with httpx.Client(timeout=15.0, headers=self.headers, follow_redirects=True) as client:
                resp = client.get(search_url)
                if resp.status_code != 200: return None
                soup = BeautifulSoup(resp.text, "html.parser")
                price_elems = soup.find_all(text=lambda t: '₦' in t or 'NGN' in t)
                for elem in price_elems:
                    price_str = elem.strip().replace('₦', '').replace(',', '').replace('NGN', '').strip()
                    try:
                        price = float(price_str)
                        if price > 0: return {"price": price, "url": search_url}
                    except ValueError: continue
                return None
        except Exception as e:
            logger.error(f"Jiji scraper failed for {material_name}: {e}")
            return None

class PriceEngine:
    def __init__(self):
        self.scrapers: list[BaseScraper] = [
            CutstructScraper(),
            JijiScraper(),
            NigerianPriceScraper(),
            BuildersMartScraper()
        ]

    def update_all_materials(self, material_list: list[str]):
        for material in material_list:
            for scraper in self.scrapers:
                price_data = scraper.scrape_material(material)
                if price_data:
                    scraper._persist_price(
                        material_name=material,
                        price=price_data["price"],
                        url=price_data["url"]
                    )

price_engine = PriceEngine()
