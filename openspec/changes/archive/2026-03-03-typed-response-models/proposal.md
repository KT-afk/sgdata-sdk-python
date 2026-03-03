## Why

The SDK currently returns raw `Dict[str, Any]` for all endpoints, forcing every consumer to know the API's undocumented quirks — especially the carpark endpoint where numeric fields are returned as strings (e.g., `"lots_available": "50"`). This makes the SDK barely more useful than calling `requests` directly.

## What Changes

- **BREAKING**: All `SGDataClient` methods now return Pydantic model instances instead of raw dicts
- Add `models/` subpackage with typed response models for all 9 endpoints
- Add enums for `LotType` (C/Y/H/S) and `Region` (west/east/central/south/north/national)
- Carpark models auto-coerce string numbers to `int`, string datetimes to `datetime`
- Computed properties on carpark models: `occupancy_rate`, `is_full`, `total_available`, `car_lots`
- Convenience methods on response objects: `get(id)`, `available()`, `full()`
- All `date_time` / `date` parameters now accept `datetime | date | str` (formatted internally)
- Custom exception hierarchy: `SGDataError`, `RateLimitError`, `SGDataTimeoutError`
- Built-in retry with exponential backoff on transient failures (configurable, off by default)
- `.raw` property on every response for escape hatch to original dict

## Capabilities

### New Capabilities

- `carpark-response-models`: Typed Pydantic models for carpark availability — `LotType`, `LotInfo`, `Carpark`, `CarparkAvailabilityResponse` with computed properties and convenience methods
- `environment-response-models`: Typed Pydantic models for air quality (PSI, PM2.5) and weather (forecasts, rainfall, humidity, temperature) endpoints
- `datetime-inputs`: Accept `datetime | date | str` for all `date_time` and `date` parameters
- `retry-resilience`: Configurable retry logic with exponential backoff for transient API failures
- `custom-exceptions`: SDK-specific exception hierarchy wrapping `requests` errors

### Modified Capabilities

<!-- No existing specs to modify — first version -->

## Impact

- **Breaking change**: Return types change from `dict` to Pydantic models (v0.1.0 → v0.2.0)
- **New dependency**: `pydantic>=2.0`
- **New optional dependency**: `tenacity` (for retry support, under `sgdata-sdk[retry]`)
- **Code affected**: `sgdata/client.py`, `sgdata/__init__.py`
- **New files**: `sgdata/models/`, `sgdata/exceptions.py`
- **Tests**: All existing mock tests need updating for new return types; new tests for model coercion
