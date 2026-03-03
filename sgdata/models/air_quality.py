"""Air quality response models for PSI and PM2.5 data."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional, Union

from pydantic import ConfigDict

from sgdata.models.base import BaseResponse


class Region(str, Enum):
    """Geographic regions used in air quality readings."""

    WEST = "west"
    EAST = "east"
    CENTRAL = "central"
    SOUTH = "south"
    NORTH = "north"
    NATIONAL = "national"


class PSIReading(BaseResponse):
    """PSI pollutant readings across all regions for a single timestamp."""

    model_config = ConfigDict(extra="ignore")

    o3_sub_index: Dict[Region, Union[int, float]]
    pm10_twenty_four_hourly: Dict[Region, Union[int, float]]
    pm10_sub_index: Dict[Region, Union[int, float]]
    co_sub_index: Dict[Region, Union[int, float]]
    pm25_twenty_four_hourly: Dict[Region, Union[int, float]]
    so2_sub_index: Dict[Region, Union[int, float]]
    co_eight_hour_max: Dict[Region, Union[int, float]]
    no2_one_hour_max: Dict[Region, Union[int, float]]
    so2_twenty_four_hourly: Dict[Region, Union[int, float]]
    pm25_sub_index: Dict[Region, Union[int, float]]
    psi_twenty_four_hourly: Dict[Region, Union[int, float]]
    o3_eight_hour_max: Dict[Region, Union[int, float]]

    @property
    def psi_24h(self) -> Dict[Region, Union[int, float]]:
        """Alias for psi_twenty_four_hourly."""
        return self.psi_twenty_four_hourly

    @property
    def pm25_24h(self) -> Dict[Region, Union[int, float]]:
        """Alias for pm25_twenty_four_hourly."""
        return self.pm25_twenty_four_hourly

    @property
    def pm10_24h(self) -> Dict[Region, Union[int, float]]:
        """Alias for pm10_twenty_four_hourly."""
        return self.pm10_twenty_four_hourly


def _parse_region_dict(
    raw_dict: Dict[str, Any],
) -> Dict[Region, Union[int, float]]:
    """Convert string-keyed dict to Region-keyed dict."""
    return {Region(k): v for k, v in raw_dict.items()}


class PSIResponse(BaseResponse):
    """Parsed response from the PSI API endpoint."""

    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    update_timestamp: datetime
    readings: PSIReading

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PSIResponse":
        """Parse the raw PSI API response dict into a PSIResponse.

        Args:
            data: Raw API response dict.

        Returns:
            Populated PSIResponse instance.
        """
        item = data["items"][0]
        timestamp = datetime.fromisoformat(item["timestamp"])
        update_timestamp = datetime.fromisoformat(item["update_timestamp"])

        raw_readings = item["readings"]
        readings_data = {
            field: _parse_region_dict(raw_readings[field])
            for field in raw_readings
        }

        readings = PSIReading(**readings_data, raw=raw_readings)

        return cls(
            timestamp=timestamp,
            update_timestamp=update_timestamp,
            readings=readings,
            raw=data,
        )


class PM25Reading(BaseResponse):
    """PM2.5 one-hourly readings across all regions."""

    model_config = ConfigDict(extra="ignore")

    pm25_one_hourly: Dict[Region, int]


class PM25Response(BaseResponse):
    """Parsed response from the PM2.5 API endpoint."""

    model_config = ConfigDict(extra="ignore")

    timestamp: datetime
    readings: PM25Reading

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PM25Response":
        """Parse the raw PM2.5 API response dict into a PM25Response.

        Args:
            data: Raw API response dict.

        Returns:
            Populated PM25Response instance.
        """
        item = data["items"][0]
        timestamp = datetime.fromisoformat(item["timestamp"])

        raw_readings = item["readings"]
        pm25_one_hourly: Dict[Region, int] = {
            Region(k): int(v) for k, v in raw_readings["pm25_one_hourly"].items()
        }

        readings = PM25Reading(
            pm25_one_hourly=pm25_one_hourly,
            raw=raw_readings,
        )

        return cls(
            timestamp=timestamp,
            readings=readings,
            raw=data,
        )
