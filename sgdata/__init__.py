"""SGData SDK - Python client for Singapore Government Data APIs."""

from sgdata.client import SGDataClient
from sgdata.exceptions import (
    RateLimitError,
    SGDataAPIError,
    SGDataError,
    SGDataTimeoutError,
)
from sgdata.models import (
    AreaForecast,
    BaseResponse,
    Carpark,
    CarparkAvailabilityResponse,
    LotInfo,
    LotType,
    PM25Reading,
    PM25Response,
    PSIReading,
    PSIResponse,
    Region,
    StationReading,
    StationReadingResponse,
    WeatherForecastResponse,
)

__version__ = "0.2.0"
__all__ = [
    # Client
    "SGDataClient",
    # Exceptions
    "SGDataError",
    "SGDataAPIError",
    "RateLimitError",
    "SGDataTimeoutError",
    # Models
    "BaseResponse",
    "Region",
    "PSIReading",
    "PSIResponse",
    "PM25Reading",
    "PM25Response",
    "LotType",
    "LotInfo",
    "Carpark",
    "CarparkAvailabilityResponse",
    "AreaForecast",
    "WeatherForecastResponse",
    "StationReading",
    "StationReadingResponse",
]
