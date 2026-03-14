from datetime import UTC, datetime
from typing import Any

import httpx
import redis
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.models import WeatherLog
from app.db.session import SessionLocal

WEATHER_URL = "https://api.openweathermap.org/data/3.0/onecall"

CITY_COORDS: dict[str, tuple[float, float]] = {
    "lagos": (6.5244, 3.3792),
    "abuja": (9.0765, 7.3986),
    "port harcourt": (4.8156, 7.0498),
    "kano": (12.0022, 8.5920),
    "enugu": (6.4584, 7.5464),
}


class WeatherService:
    def __init__(self) -> None:
        self._redis = None
        try:
            self._redis = redis.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            self._redis = None

    def _cache_get(self, key: str) -> dict[str, Any] | None:
        if not self._redis:
            return None
        try:
            raw = self._redis.get(key)
            if raw:
                import json

                return json.loads(raw)
        except Exception:
            return None
        return None

    def _cache_set(self, key: str, value: dict[str, Any]) -> None:
        if not self._redis:
            return
        import json

        try:
            self._redis.setex(key, settings.weather_cache_ttl, json.dumps(value))
        except Exception:
            return

    def _fallback(self, city: str) -> dict[str, Any]:
        return {
            "city": city,
            "temperature_c": 30.0,
            "rainfall_mm": 0.0,
            "wind_speed_kmh": 12.0,
            "humidity_pct": 72.0,
            "weather_condition": "unknown",
            "source": "fallback",
            "fetched_at": datetime.now(UTC).isoformat(),
        }

    def fetch_city_weather(self, city: str) -> dict[str, Any]:
        cache_key = f"weather:{city.lower()}"
        cached = self._cache_get(cache_key)
        if cached:
            return cached

        api_key = settings.openweather_api_key or settings.weather_api_key
        if not api_key:
            data = self._fallback(city)
            self._cache_set(cache_key, data)
            return data

        city_key = city.strip().lower()
        coords = CITY_COORDS.get(city_key)
        if coords is None:
            data = self._fallback(city)
            self._cache_set(cache_key, data)
            self._persist(data)
            return data

        lat, lon = coords
        try:
            with httpx.Client(timeout=15.0) as client:
                resp = client.get(
                    WEATHER_URL,
                    params={
                        "lat": lat,
                        "lon": lon,
                        "exclude": settings.openweather_exclude_parts,
                        "appid": api_key,
                        "units": "metric",
                    },
                )
                resp.raise_for_status()
                body = resp.json()
            current = body.get("current", {})
            rainfall = 0.0
            rain_obj = current.get("rain")
            if isinstance(rain_obj, dict):
                rainfall = float(rain_obj.get("1h", 0.0))
            elif isinstance(rain_obj, (int, float)):
                rainfall = float(rain_obj)

            data = {
                "city": city,
                "temperature_c": float(current.get("temp", 30.0)),
                "rainfall_mm": rainfall,
                "wind_speed_kmh": float(current.get("wind_speed", 0.0)) * 3.6,
                "humidity_pct": float(current.get("humidity", 0.0)),
                "weather_condition": (current.get("weather") or [{}])[0].get("main", "unknown"),
                "source": "openweather_onecall_3",
                "fetched_at": datetime.now(UTC).isoformat(),
            }
            self._cache_set(cache_key, data)
            self._persist(data)
            return data
        except Exception:
            data = self._fallback(city)
            self._cache_set(cache_key, data)
            self._persist(data)
            return data

    def fetch_all_configured_cities(self) -> list[dict[str, Any]]:
        cities = [c.strip() for c in settings.weather_cities.split(",") if c.strip()]
        return [self.fetch_city_weather(city) for city in cities]

    def _persist(self, data: dict[str, Any]) -> None:
        db: Session = SessionLocal()
        try:
            db.add(
                WeatherLog(
                    city=data["city"],
                    temperature_c=data["temperature_c"],
                    rainfall_mm=data["rainfall_mm"],
                    wind_speed_kmh=data["wind_speed_kmh"],
                    humidity_pct=data["humidity_pct"],
                    condition=data["weather_condition"],
                )
            )
            db.commit()
        except Exception:
            db.rollback()
        finally:
            db.close()


weather_service = WeatherService()
