# SGData SDK

A Python client for Singapore's government data APIs. Get typed, ready-to-use data for weather, air quality, and carpark availability — no dict wrangling required.

## Features

- Typed responses for all 9 endpoints — full autocomplete, no raw dicts
- Auto-coercion of API quirks (string numbers, string datetimes)
- Convenience methods on responses: `available()`, `get()`, `full()`
- SDK exceptions instead of bare `requests` errors
- Pass `datetime` objects or strings for historical queries
- Optional retry with exponential backoff

## Installation

```bash
pip install sgdata-sdk
```

## Quick Start

```python
from sgdata import SGDataClient

client = SGDataClient()

# Typed responses — no dict drilling
psi = client.get_psi()
print(psi.readings.psi_24h)          # dict[Region, int]
print(psi.timestamp)                  # datetime

weather = client.get_2hour_weather_forecast()
ang_mo_kio = weather.get("Ang Mo Kio")
print(ang_mo_kio.forecast)            # "Partly Cloudy"
print(ang_mo_kio.latitude)            # 1.375

carparks = client.get_carpark_availability()
print(carparks.timestamp)             # datetime
```

## Carpark Availability

The carpark endpoint is where the SDK saves the most work:

```python
carparks = client.get_carpark_availability()

# All carparks with available spaces
for cp in carparks.available():
    print(cp.carpark_number, cp.total_available)

# Only carparks with available car lots
from sgdata import LotType
for cp in carparks.available(lot_type=LotType.CAR):
    print(cp.carpark_number, cp.car_lots.available_lots)

# Look up a specific carpark
hg1 = carparks.get("HG1")
if hg1:
    print(f"{hg1.carpark_number}: {hg1.car_lots.occupancy_rate:.0%} full")

# All full carparks
full = carparks.full()
```

## What You Can Get

**Air Quality**
- `get_psi()` → `PSIResponse` — Pollutant Standards Index
- `get_pm25()` → `PM25Response` — PM2.5 readings

**Weather Forecasts**
- `get_2hour_weather_forecast()` → `WeatherForecastResponse`
- `get_24hour_weather_forecast()` → `WeatherForecastResponse`
- `get_4day_weather_forecast()` → `WeatherForecastResponse`

**Weather Measurements**
- `get_rainfall()` → `StationReadingResponse`
- `get_relative_humidity()` → `StationReadingResponse`
- `get_air_temperature()` → `StationReadingResponse`

**Transport**
- `get_carpark_availability()` → `CarparkAvailabilityResponse`

## Historical Data

Pass a `datetime`, `date`, or a string:

```python
from datetime import datetime, date

# datetime object
psi = client.get_psi(date_time=datetime(2024, 1, 15, 12))

# date object
psi = client.get_psi(date=date(2024, 1, 15))

# or a string, same as before
psi = client.get_psi(date_time="2024-01-15T12:00:00")
```

## Error Handling

```python
from sgdata import SGDataError, SGDataAPIError, RateLimitError, SGDataTimeoutError

try:
    carparks = client.get_carpark_availability()
except RateLimitError:
    print("Rate limited — back off and retry")
except SGDataTimeoutError:
    print("Request timed out")
except SGDataAPIError as e:
    print(f"API error {e.status_code}: {e}")
except SGDataError as e:
    print(f"SDK error: {e}")
```

## Context Manager

```python
with SGDataClient() as client:
    weather = client.get_2hour_weather_forecast()
    temp = client.get_air_temperature()
```

## Retry Support

```bash
pip install sgdata-sdk[retry]
```

```python
# Automatically retries on 429, 5xx, and timeouts (3 attempts, exponential backoff)
client = SGDataClient(retry=True)
```

## Type Reference

### CarparkAvailabilityResponse

| Field | Type | Description |
|-------|------|-------------|
| `carparks` | `List[Carpark]` | All carpark records |
| `timestamp` | `datetime` | API response timestamp |
| `raw` | `Dict` | Raw API response |

**Methods:** `get(carpark_number)` → `Carpark | None`, `available(lot_type=None)` → `List[Carpark]`, `full()` → `List[Carpark]`

### Carpark

| Field | Type | Description |
|-------|------|-------------|
| `carpark_number` | `str` | Carpark ID (e.g., "HE12") |
| `lots` | `List[LotInfo]` | Availability by lot type |
| `updated_at` | `datetime` | Last updated time |
| `car_lots` | `LotInfo \| None` (property) | Shortcut for type `'C'` lots |
| `total_available` | `int` (property) | Sum of all available lots |
| `is_full` | `bool` (property) | True if no lots available |

### LotInfo

| Field | Type | Description |
|-------|------|-------------|
| `total_lots` | `int` | Total capacity |
| `available_lots` | `int` | Currently available |
| `lot_type` | `LotType` | Lot category |
| `occupancy_rate` | `float` (property) | Usage ratio (0.0–1.0) |

### LotType (Enum)

| Value | Description |
|-------|-------------|
| `'C'` | Car |
| `'Y'` | Motorcycle |
| `'H'` | Heavy vehicle |
| `'S'` | Season parking |

### PSIResponse

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` | Reading timestamp |
| `update_timestamp` | `datetime` | Last API update time |
| `readings` | `PSIReading` | All pollutant readings |
| `raw` | `Dict` | Raw API response |

### PSIReading

| Field | Type | Description |
|-------|------|-------------|
| `psi_twenty_four_hourly` | `Dict[Region, int\|float]` | 24-hour PSI |
| `pm25_twenty_four_hourly` | `Dict[Region, int\|float]` | 24-hour PM2.5 |
| `pm10_twenty_four_hourly` | `Dict[Region, int\|float]` | 24-hour PM10 |
| `o3_sub_index` | `Dict[Region, int\|float]` | Ozone sub-index |
| `co_sub_index` | `Dict[Region, int\|float]` | CO sub-index |
| `so2_sub_index` | `Dict[Region, int\|float]` | SO2 sub-index |
| `co_eight_hour_max` | `Dict[Region, int\|float]` | 8-hour max CO |
| `no2_one_hour_max` | `Dict[Region, int\|float]` | 1-hour max NO2 |
| `so2_twenty_four_hourly` | `Dict[Region, int\|float]` | 24-hour SO2 |
| `pm25_sub_index` | `Dict[Region, int\|float]` | PM2.5 sub-index |
| `pm10_sub_index` | `Dict[Region, int\|float]` | PM10 sub-index |
| `o3_eight_hour_max` | `Dict[Region, int\|float]` | 8-hour max ozone |

**Aliases:** `psi_24h`, `pm25_24h`, `pm10_24h`

### PM25Response

| Field | Type | Description |
|-------|------|-------------|
| `timestamp` | `datetime` | Reading timestamp |
| `readings` | `PM25Reading` | PM2.5 readings |
| `raw` | `Dict` | Raw API response |

### PM25Reading

| Field | Type | Description |
|-------|------|-------------|
| `pm25_one_hourly` | `Dict[Region, int]` | 1-hour PM2.5 by region |

### WeatherForecastResponse

| Field | Type | Description |
|-------|------|-------------|
| `forecasts` | `List[AreaForecast]` | Per-area forecasts |
| `valid_from` | `datetime` | Forecast validity start |
| `valid_to` | `datetime \| None` | Forecast validity end |
| `timestamp` | `datetime` | API response timestamp |
| `raw` | `Dict` | Raw API response |

**Methods:** `get(area_name)` → `AreaForecast | None`

### AreaForecast

| Field | Type | Description |
|-------|------|-------------|
| `area` | `str` | Area name (e.g., "Ang Mo Kio") |
| `forecast` | `str` | Forecast text (e.g., "Partly Cloudy") |
| `latitude` | `float` | Area latitude |
| `longitude` | `float` | Area longitude |

### StationReadingResponse

| Field | Type | Description |
|-------|------|-------------|
| `readings` | `List[StationReading]` | Per-station readings |
| `timestamp` | `datetime` | API response timestamp |
| `raw` | `Dict` | Raw API response |

### StationReading

| Field | Type | Description |
|-------|------|-------------|
| `station_id` | `str` | Station ID |
| `station_name` | `str` | Station name |
| `latitude` | `float` | Station latitude |
| `longitude` | `float` | Station longitude |
| `value` | `float` | Reading value |
| `timestamp` | `datetime` | Reading timestamp |

### Region (Enum)

| Value | Description |
|-------|-------------|
| `'west'` | West region |
| `'east'` | East region |
| `'central'` | Central region |
| `'south'` | South region |
| `'north'` | North region |
| `'national'` | National average |

## Development

```bash
git clone https://github.com/KT-afk/sgdata-sdk-python.git
cd sgdata-sdk-python
pip install -e ".[dev]"

pytest          # run tests
mypy sgdata     # type check
black sgdata tests
```

## License

MIT

## Links

- Data source: [data.gov.sg](https://data.gov.sg)
- Issues and PRs welcome!
