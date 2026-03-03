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
