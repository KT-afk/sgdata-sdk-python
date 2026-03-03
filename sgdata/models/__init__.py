"""SGData SDK response models.

Public API — all models and enums are importable directly from sgdata.models.
"""

from sgdata.models.air_quality import (
    PM25Reading,
    PM25Response,
    PSIReading,
    PSIResponse,
    Region,
)
from sgdata.models.base import BaseResponse
from sgdata.models.carpark import (
    Carpark,
    CarparkAvailabilityResponse,
    LotInfo,
    LotType,
)
from sgdata.models.weather import (
    AreaForecast,
    StationReading,
    StationReadingResponse,
    WeatherForecastResponse,
)

__all__ = [
    # Base
    "BaseResponse",
    # Air quality
    "Region",
    "PSIReading",
    "PSIResponse",
    "PM25Reading",
    "PM25Response",
    # Carpark
    "LotType",
    "LotInfo",
    "Carpark",
    "CarparkAvailabilityResponse",
    # Weather
    "AreaForecast",
    "WeatherForecastResponse",
    "StationReading",
    "StationReadingResponse",
]
