## Context

The SDK wraps 9 data.gov.sg API endpoints and currently returns raw `Dict[str, Any]` from every method. The primary consumer is a Flask-based carpark availability web app that must traverse deeply nested dicts and cast string fields to integers manually.

The carpark endpoint is the most painful: `lots_available` and `total_lots` are returned as strings despite being numeric. The API also uses single-character lot type codes (`"C"`, `"Y"`, `"H"`, `"S"`) with no documentation in the response.

Stack: Flask (sync), Python ≥ 3.8, Pydantic v2.

## Goals / Non-Goals

**Goals:**
- Replace `Dict[str, Any]` return types with typed Pydantic models across all 9 endpoints
- Auto-coerce API quirks (string numbers, string datetimes) in the model layer
- Surface computed properties useful to the web app (occupancy rate, is_full, car_lots shortcut)
- Accept `datetime | date | str` for all temporal parameters
- Add SDK-specific exception types
- Add optional retry/backoff support

**Non-Goals:**
- Async client (future)
- Caching layer (future)
- Temporal integration (future, optional contrib)
- Coverage of additional data.gov.sg endpoints beyond the current 9

## Decisions

### Decision 1: Pydantic v2 over stdlib dataclasses

**Choice**: Pydantic v2

**Rationale**: The carpark API returns numeric fields as strings. Pydantic's automatic coercion (`str → int`, `str → datetime`) means zero manual casting code in models. Dataclasses would require `__post_init__` coercion methods for every field. Pydantic also provides `.model_dump()` for free, which is what Flask routes need to produce JSON responses.

**Alternative considered**: stdlib dataclasses with custom `from_dict()` classmethods. Rejected — more boilerplate, no coercion, no serialization.

### Decision 2: Break backwards compatibility (v0.1.0 → v0.2.0)

**Choice**: Return types change from `dict` to models — no compatibility shim.

**Rationale**: The project is at v0.1.0 (pre-release). The primary consumer is a single web app maintained by the same developer. Adding a compatibility layer just to return dicts would undermine the entire value of this change and add ongoing maintenance burden.

**Mitigation**: Every response model exposes `.raw` — the original dict — as an escape hatch.

### Decision 3: Models package structure

```
sgdata/
├── client.py
├── exceptions.py
└── models/
    ├── __init__.py       ← re-exports all public models
    ├── base.py           ← BaseResponse with .raw
    ├── carpark.py        ← LotType, LotInfo, Carpark, CarparkAvailabilityResponse
    ├── air_quality.py    ← PSIResponse, PM25Response + shared Region enum
    └── weather.py        ← ForecastResponse, StationReadingResponse
```

**Rationale**: Groups by domain (matching the API's `/environment` and `/transport` paths). Keeps `client.py` unchanged except for return type annotations.

### Decision 4: Retry via tenacity (optional extra)

**Choice**: `tenacity` library, exposed as `pip install sgdata-sdk[retry]`

**Rationale**: Tenacity is the de-facto Python retry library. Making it optional keeps the core install lightweight. The `SGDataClient` accepts a `retry` boolean (default `False`) that activates automatic retries on transient errors (5xx, timeout).

**Alternative considered**: Manual retry loop using `time.sleep`. Rejected — tenacity handles exponential backoff and jitter correctly; no need to reinvent it.

### Decision 5: datetime input handling

Accept `Union[datetime, date, str]` for `date_time` and `date` parameters. Format internally using `isoformat()`. Validation raises `ValueError` for unparseable strings (not a custom SDK exception — this is a programming error, not a runtime API error).

## Risks / Trade-offs

- **Pydantic v2 adds ~5MB to install size** → Acceptable; Pydantic v2 is ubiquitous in the Python ecosystem
- **API response shape changes break models silently** → Mitigated by `.raw` escape hatch and tests against fixture data; models use `model_config = ConfigDict(extra='ignore')` so unknown fields don't crash
- **String coercion hides bad API data** → Acceptable trade-off; raw data always accessible via `.raw`
- **tenacity as optional dep creates two install modes** → Documented clearly; retry=True raises ImportError with a helpful message if tenacity not installed

## Migration Plan

1. Add `pydantic>=2.0` to `dependencies` in `pyproject.toml`
2. Add `tenacity>=8.0` to `optional-dependencies.retry`
3. Create `sgdata/exceptions.py`
4. Create `sgdata/models/` package
5. Update `sgdata/client.py` — change return type annotations, parse responses through models
6. Update `sgdata/__init__.py` — export models and exceptions
7. Update all tests — mock responses now need to match model parsing; add coercion tests
8. Bump version to `0.2.0`

Rollback: `pip install sgdata-sdk==0.1.0` — no DB migrations or infra changes involved.

## Open Questions

- Should `StationReadingResponse` (rainfall/humidity/temperature) include station geolocation? The API returns coordinates in `metadata.stations` — surfacing them as `station.latitude / station.longitude` on each reading seems useful but adds model complexity.
- Retry default: `False` means opt-in. Should the SDK default to retrying once on 429/5xx? The data.gov.sg API doesn't publish rate limits, so defaulting to retry-on-429 might be safer than not.
