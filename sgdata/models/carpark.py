"""Carpark availability response models for the SGData SDK."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, computed_field, field_validator

from sgdata.models.base import BaseResponse


class LotType(str, Enum):
    """Carpark lot type codes returned by the API."""

    CAR = "C"
    MOTORCYCLE = "Y"
    HEAVY_VEHICLE = "H"
    SPECIAL = "S"


class LotInfo(BaseModel):
    """Information about a single lot type within a carpark."""

    model_config = ConfigDict(extra="ignore")

    total_lots: int
    available_lots: int
    lot_type: LotType

    @field_validator("total_lots", mode="before")
    @classmethod
    def coerce_total_lots(cls, v: Any) -> int:
        return int(v)

    @field_validator("available_lots", mode="before")
    @classmethod
    def coerce_available_lots(cls, v: Any) -> int:
        return int(v)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def occupancy_rate(self) -> float:
        """Fraction of available lots out of total lots (0.0 when total is 0)."""
        if self.total_lots == 0:
            return 0.0
        return self.available_lots / self.total_lots

    @classmethod
    def _from_api(cls, data: Dict[str, Any]) -> "LotInfo":
        return cls(
            total_lots=data["total_lots"],
            available_lots=data["lots_available"],
            lot_type=LotType(data["lot_type"]),
        )


class Carpark(BaseModel):
    """A single carpark with its lot availability data."""

    model_config = ConfigDict(extra="ignore")

    carpark_number: str
    lots: List[LotInfo]
    updated_at: datetime

    @computed_field  # type: ignore[prop-decorator]
    @property
    def car_lots(self) -> Optional[LotInfo]:
        """First LotInfo entry whose lot_type is CAR, or None."""
        for lot in self.lots:
            if lot.lot_type == LotType.CAR:
                return lot
        return None

    @computed_field  # type: ignore[prop-decorator]
    @property
    def total_available(self) -> int:
        """Sum of available_lots across all lot types."""
        return sum(lot.available_lots for lot in self.lots)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def is_full(self) -> bool:
        """True when no lots of any type are available."""
        return self.total_available == 0

    @classmethod
    def _from_api(cls, data: Dict[str, Any]) -> "Carpark":
        return cls(
            carpark_number=data["carpark_number"],
            updated_at=datetime.fromisoformat(data["update_datetime"]),
            lots=[LotInfo._from_api(info) for info in data["carpark_info"]],
        )


class CarparkAvailabilityResponse(BaseResponse):
    """Parsed response from the carpark availability endpoint."""

    carparks: List[Carpark]
    timestamp: datetime

    def get(self, number: str) -> Optional[Carpark]:
        """Return the carpark matching *number*, or None if not found."""
        for carpark in self.carparks:
            if carpark.carpark_number == number:
                return carpark
        return None

    def available(self, lot_type: Optional[LotType] = None) -> List[Carpark]:
        """Return carparks that have available lots.

        When *lot_type* is None, any carpark with total_available > 0 qualifies.
        When *lot_type* is specified, only carparks whose matching lot has
        available_lots > 0 are returned.
        """
        result: List[Carpark] = []
        for carpark in self.carparks:
            if lot_type is None:
                if carpark.total_available > 0:
                    result.append(carpark)
            else:
                lot = carpark.car_lots if lot_type == LotType.CAR else next(
                    (l for l in carpark.lots if l.lot_type == lot_type), None
                )
                if lot is not None and lot.available_lots > 0:
                    result.append(carpark)
        return result

    def full(self) -> List[Carpark]:
        """Return carparks where every lot type is at capacity."""
        return [c for c in self.carparks if c.is_full]

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "CarparkAvailabilityResponse":
        """Construct a CarparkAvailabilityResponse from the raw API dict."""
        item = data["items"][0]
        timestamp = datetime.fromisoformat(item["timestamp"])
        carparks = [Carpark._from_api(entry) for entry in item["carpark_data"]]
        return cls(raw=data, timestamp=timestamp, carparks=carparks)
