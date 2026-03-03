## 1. Project Setup

- [x] 1.1 Add `pydantic>=2.0` to `dependencies` in `pyproject.toml`
- [x] 1.2 Add `tenacity>=8.0` to `optional-dependencies.retry` in `pyproject.toml`
- [x] 1.3 Add `pydantic` and `types-requests` to dev dependencies
- [x] 1.4 Bump version to `0.2.0` in `pyproject.toml` and `sgdata/__init__.py`

## 2. Custom Exceptions

- [x] 2.1 Create `sgdata/exceptions.py` with `SGDataError` base class
- [x] 2.2 Add `SGDataAPIError(SGDataError)` with `.status_code` and `.response` attributes
- [x] 2.3 Add `RateLimitError(SGDataError)` with `.response` attribute
- [x] 2.4 Add `SGDataTimeoutError(SGDataError)`

## 3. Base Models

- [x] 3.1 Create `sgdata/models/` package with `__init__.py`
- [x] 3.2 Create `sgdata/models/base.py` with `BaseResponse` (Pydantic BaseModel with `raw: dict` field)

## 4. Carpark Models

- [x] 4.1 Create `sgdata/models/carpark.py` with `LotType` string enum (C/Y/H/S)
- [x] 4.2 Implement `LotInfo` model with int coercion for `total_lots`/`available_lots` and `occupancy_rate` computed property
- [x] 4.3 Implement `Carpark` model with `car_lots`, `total_available`, `is_full` properties and `updated_at` datetime coercion
- [x] 4.4 Implement `CarparkAvailabilityResponse` with `get()`, `available()`, `full()` methods and `timestamp` datetime

## 5. Air Quality Models

- [x] 5.1 Create `sgdata/models/air_quality.py` with `Region` string enum (west/east/central/south/north/national)
- [x] 5.2 Implement `PSIReading` model with all 12 pollutant fields as `dict[Region, int | float]`
- [x] 5.3 Implement `PSIResponse` with `timestamp`, `readings: PSIReading`, and `raw`
- [x] 5.4 Implement `PM25Reading` and `PM25Response` models

## 6. Weather Models

- [x] 6.1 Create `sgdata/models/weather.py` with `AreaForecast` model (merges area_metadata coordinates)
- [x] 6.2 Implement `WeatherForecastResponse` with `get()` method and `valid_from`/`valid_to` datetimes — reused by 2hr, 24hr, 4day endpoints
- [x] 6.3 Implement `StationReading` model with geolocation fields
- [x] 6.4 Implement `StationReadingResponse` — reused by rainfall, humidity, temperature endpoints

## 7. Update Client

- [x] 7.1 Update `_request()` to raise SDK exceptions (`RateLimitError` on 429, `SGDataAPIError` on other HTTP errors, `SGDataTimeoutError` on timeout)
- [x] 7.2 Update `_build_params()` to accept `datetime | date | str | None` and format to string internally
- [x] 7.3 Update all 9 endpoint methods to parse raw dict through appropriate response model and return typed model
- [x] 7.4 Add `retry: bool = False` parameter to `__init__`; raise `ImportError` with install hint when `retry=True` and tenacity not installed
- [x] 7.5 Implement retry logic using `tenacity` (3 attempts, exponential backoff, retry on 429/5xx/timeout only)

## 8. Update Exports

- [x] 8.1 Update `sgdata/models/__init__.py` to re-export all public models and enums
- [x] 8.2 Update `sgdata/__init__.py` to export models, enums, and exceptions alongside `SGDataClient`

## 9. Update Tests

- [x] 9.1 Update existing `TestHTTPRequests` tests — assert SDK exceptions raised instead of `requests` exceptions
- [x] 9.2 Update all endpoint tests to assert return type is a model instance, not a dict
- [x] 9.3 Add `TestCarparkModels` — test string→int coercion, `occupancy_rate`, `is_full`, `car_lots`, `total_available`
- [x] 9.4 Add `TestCarparkAvailabilityResponse` — test `get()`, `available()`, `available(lot_type=...)`, `full()`
- [x] 9.5 Add `TestAirQualityModels` — test `PSIResponse`, `PM25Response` with fixture data from conftest
- [x] 9.6 Add `TestWeatherModels` — test `WeatherForecastResponse.get()`, `valid_from`/`valid_to`, `StationReadingResponse`
- [x] 9.7 Add `TestDatetimeInputs` — test `datetime`, `date`, and `str` inputs all produce correct query params
- [x] 9.8 Add `TestRetryResilience` — test retry on 500/503, no retry on 404, ImportError when tenacity missing
- [x] 9.9 Verify all tests pass: `pytest`
- [x] 9.10 Verify type checking: `mypy sgdata`
