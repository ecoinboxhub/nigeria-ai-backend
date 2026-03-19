from datetime import UTC, datetime
from typing import Any
import logging
import json

import httpx
import redis

from app.core.config import settings
from app.db.supabase import supabase

logger = logging.getLogger(__name__)

# Primary Source: WeatherAPI.com
WEATHER_API_URL = "http://api.weatherapi.com/v1/current.json"

# Secondary Source: OpenWeatherMap
OPENWEATHER_URL = "https://api.openweathermap.org/data/2.5/weather"

# Emergency Source: Open-Meteo (No Key)
OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"

CITY_COORDS: dict[str, tuple[float, float]] = {
    "lagos": (6.5244, 3.3792),
    "abuja": (9.0765, 7.3986),
    "port harcourt": (4.8156, 7.0498),
    "kano": (12.0022, 8.5920),
    "enugu": (6.4584, 7.5464),
    "ibadan": (7.3775, 3.9470),
}

class WeatherService:
    def __init__(self) -> None:
        self._redis = None
        try:
            if settings.redis_url:
                r = redis.from_url(settings.redis_url, decode_responses=True)
                r.ping()
                self._redis = r
        except Exception as e:
            logger.warning(f"WeatherService: Redis unavailable, caching disabled. {e}")
            self._redis = None

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        if not self._redis: return None
        try:
            raw = self._redis.get(key)
            return json.loads(raw) if raw else None
        except Exception: return None

    def _cache_set(self, key: str, value: dict[str, Any]) -> None:
        if not self._redis: return
        try:
            self._redis.setex(key, settings.weather_cache_ttl, json.dumps(value))
        except Exception: pass

    def _try_weather_api(self, city: str) -> dict[str, Any] | None:
        """Tier 1: WeatherAPI.com"""
        if not settings.weather_api_key: return None
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    WEATHER_API_URL,
                    params={"key": settings.weather_api_key, "q": city, "aqi": "no"}
                )
                if resp.status_code != 200: return None
                body = resp.json()
                current = body.get("current", {})
                return {
                    "city": city,
                    "temperature_c": current.get("temp_c"),
                    "rainfall_mm": current.get("precip_mm", 0.0),
                    "wind_speed_kmh": current.get("wind_kph"),
                    "humidity_pct": current.get("humidity"),
                    "weather_condition": current.get("condition", {}).get("text", "unknown"),
                    "source": "weatherapi.com",
                    "fetched_at": datetime.now(UTC).isoformat(),
                }
        except Exception as e:
            logger.error(f"WeatherAPI failed for {city}: {e}")
            return None

    def _try_openweather(self, city: str) -> dict[str, Any] | None:
        """Tier 2: OpenWeatherMap"""
        if not settings.openweather_api_key: return None
        coords = CITY_COORDS.get(city.lower())
        if not coords: return None
        lat, lon = coords
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    OPENWEATHER_URL,
                    params={
                        "lat": lat, "lon": lon, 
                        "appid": settings.openweather_api_key, 
                        "units": "metric"
                    }
                )
                if resp.status_code != 200: return None
                body = resp.json()
                main = body.get("main", {})
                wind = body.get("wind", {})
                rain = body.get("rain", {}).get("1h", 0.0)
                return {
                    "city": city,
                    "temperature_c": main.get("temp"),
                    "rainfall_mm": float(rain),
                    "wind_speed_kmh": wind.get("speed", 0.0) * 3.6,
                    "humidity_pct": main.get("humidity"),
                    "weather_condition": body.get("weather", [{}])[0].get("main", "unknown"),
                    "source": "openweathermap.org",
                    "fetched_at": datetime.now(UTC).isoformat(),
                }
        except Exception as e:
            logger.error(f"OpenWeather failed for {city}: {e}")
            return None

    def _try_open_meteo(self, city: str) -> dict[str, Any] | None:
        """Tier 3: Open-Meteo (Emergency Hub - No Key)"""
        coords = CITY_COORDS.get(city.lower())
        if not coords: return None
        lat, lon = coords
        try:
            with httpx.Client(timeout=10.0) as client:
                resp = client.get(
                    OPEN_METEO_URL,
                    params={
                        "latitude": lat, "longitude": lon,
                        "current_weather": "true",
                        "timezone": "auto"
                    }
                )
                if resp.status_code != 200: return None
                body = resp.json()
                current = body.get("current_weather", {})
                return {
                    "city": city,
                    "temperature_c": current.get("temperature"),
                    "rainfall_mm": 0.0, # Basic endpoint doesn't always provide real-time rain
                    "wind_speed_kmh": current.get("windspeed"),
                    "humidity_pct": 0.0,
                    "weather_condition": "code_" + str(current.get("weathercode")),
                    "source": "open-meteo.com",
                    "fetched_at": datetime.now(UTC).isoformat(),
                }
        except Exception as e:
            logger.error(f"Open-Meteo failed for {city}: {e}")
            return None

    def fetch_city_weather(self, city: str) -> dict[str, Any]:
        cache_key = f"weather:{city.lower()}"
        cached = self._cache_get(cache_key)
        if cached: return cached

        # Try Tier 1
        data = self._try_weather_api(city)
        
        # Try Tier 2 if Tier 1 failed
        if not data:
            data = self._try_openweather(city)
            
        # Try Tier 3 if Tiers 1 & 2 failed
        if not data:
            data = self._try_open_meteo(city)

        if data:
            self._cache_set(cache_key, data)
            self._persist_to_supabase(data)
            return data
            
        # Final Fallback
        return {
            "city": city,
            "temperature_c": 30.0,
            "rainfall_mm": 0.0,
            "wind_speed_kmh": 12.0,
            "humidity_pct": 72.0,
            "weather_condition": "stable",
            "source": "hardcoded_fallback",
            "fetched_at": datetime.now(UTC).isoformat(),
        }

    def fetch_all_configured_cities(self) -> list[dict[str, Any]]:
        cities = [c.strip() for c in settings.weather_cities.split(",") if c.strip()]
        return [self.fetch_city_weather(city) for city in cities]

    def _persist_to_supabase(self, data: dict[str, Any]) -> None:
        """Persist weather log to Supabase instead of local SQL."""
        if not supabase: return
        try:
            supabase.table("weather_logs").insert({
                "city": data["city"],
                "temperature_c": data["temperature_c"],
                "rainfall_mm": data["rainfall_mm"],
                "wind_speed_kmh": data["wind_speed_kmh"],
                "humidity_pct": data["humidity_pct"],
                "condition": data["weather_condition"],
                "source": data["source"],
                "fetched_at": data["fetched_at"]
            }).execute()
        except Exception as e:
            logger.error(f"Failed to persist weather to Supabase: {e}")

weather_service = WeatherService()
