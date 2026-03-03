"""Weather forecast and station reading models for the SGData SDK."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict

from sgdata.models.base import BaseResponse


class AreaForecast(BaseModel):
    """A weather forecast for a single area, with merged coordinates."""

    model_config = ConfigDict(extra="ignore")

    area: str
    forecast: str
    latitude: float
    longitude: float


class WeatherForecastResponse(BaseResponse):
    """Parsed response from the 2hr, 24hr, and 4day weather forecast endpoints."""

    forecasts: List[AreaForecast]
    valid_from: datetime
    valid_to: Optional[datetime]
    timestamp: datetime

    def get(self, area_name: str) -> Optional[AreaForecast]:
        """Return the forecast matching *area_name* (case-sensitive), or None."""
        for forecast in self.forecasts:
            if forecast.area == area_name:
                return forecast
        return None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "WeatherForecastResponse":
        """Construct a WeatherForecastResponse from the raw API dict.

        Merges coordinates from ``area_metadata`` into each forecast entry.
        """
        # Build coordinate lookup: {area_name: {latitude, longitude}}
        coord_lookup: Dict[str, Dict[str, float]] = {}
        for meta in data.get("area_metadata", []):
            name = meta["name"]
            loc = meta.get("label_location", {})
            coord_lookup[name] = {
                "latitude": float(loc.get("latitude", 0.0)),
                "longitude": float(loc.get("longitude", 0.0)),
            }

        item = data["items"][0]
        timestamp = datetime.fromisoformat(item["timestamp"])

        valid_period = item.get("valid_period", {})
        valid_from_str = valid_period.get("start")
        valid_to_str = valid_period.get("end")

        valid_from: datetime = (
            datetime.fromisoformat(valid_from_str)
            if valid_from_str
            else timestamp
        )
        valid_to: Optional[datetime] = (
            datetime.fromisoformat(valid_to_str) if valid_to_str else None
        )

        forecasts: List[AreaForecast] = []
        for entry in item.get("forecasts", []):
            area_name = entry["area"]
            coords = coord_lookup.get(area_name, {"latitude": 0.0, "longitude": 0.0})
            forecasts.append(
                AreaForecast(
                    area=area_name,
                    forecast=entry["forecast"],
                    latitude=coords["latitude"],
                    longitude=coords["longitude"],
                )
            )

        return cls(
            raw=data,
            forecasts=forecasts,
            valid_from=valid_from,
            valid_to=valid_to,
            timestamp=timestamp,
        )


class StationReading(BaseModel):
    """A single sensor reading from a monitoring station."""

    model_config = ConfigDict(extra="ignore")

    station_id: str
    station_name: str
    latitude: float
    longitude: float
    value: float
    timestamp: datetime


class StationReadingResponse(BaseResponse):
    """Parsed response from rainfall, relative-humidity, and air-temperature endpoints."""

    readings: List[StationReading]
    timestamp: datetime

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "StationReadingResponse":
        """Construct a StationReadingResponse from the raw API dict.

        Merges station metadata (name, location) into each reading entry.
        """
        # Build station lookup: {station_id: {name, latitude, longitude}}
        station_lookup: Dict[str, Dict[str, Any]] = {}
        for station in data.get("metadata", {}).get("stations", []):
            sid = station["id"]
            loc = station.get("location", {})
            station_lookup[sid] = {
                "name": station.get("name", ""),
                "latitude": float(loc.get("latitude", 0.0)),
                "longitude": float(loc.get("longitude", 0.0)),
            }

        item = data["items"][0]
        timestamp = datetime.fromisoformat(item["timestamp"])

        readings: List[StationReading] = []
        for entry in item.get("readings", []):
            sid = entry["station_id"]
            station_info = station_lookup.get(
                sid, {"name": "", "latitude": 0.0, "longitude": 0.0}
            )
            readings.append(
                StationReading(
                    station_id=sid,
                    station_name=station_info["name"],
                    latitude=station_info["latitude"],
                    longitude=station_info["longitude"],
                    value=float(entry["value"]),
                    timestamp=timestamp,
                )
            )

        return cls(raw=data, readings=readings, timestamp=timestamp)
