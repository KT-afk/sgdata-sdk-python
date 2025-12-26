# SGData SDK

A simple Python client for accessing Singapore's government data APIs. Get weather forecasts, air quality readings, and carpark availability all in one place.

## Features

- Simple, unified client for 9 different data endpoints
- Full type hints for better autocomplete
- Get current or historical data
- Works out of the box, no config needed

## Installation

```bash
pip install sgdata-sdk
```

## Quick Start

```python
from sgdata import SGDataClient

client = SGDataClient()

# Check the air quality
psi = client.get_psi()

# Get the weather forecast
weather = client.get_2hour_weather_forecast()

# Find available parking
carparks = client.get_carpark_availability()
```

## What You Can Get

**Air Quality**
- `get_psi()` - Pollutant Standards Index
- `get_pm25()` - PM2.5 readings

**Weather Forecasts**
- `get_2hour_weather_forecast()`
- `get_24hour_weather_forecast()`
- `get_4day_weather_forecast()`

**Weather Data**
- `get_rainfall()`
- `get_relative_humidity()`
- `get_air_temperature()`

**Transport**
- `get_carpark_availability()` - HDB carpark lots

## More Examples

### Getting Historical Data

Want data from a specific time? Just pass in a date or datetime:

```python
# Get PSI from a specific date
psi = client.get_psi(date="2024-01-15")

# Or a specific time
psi = client.get_psi(date_time="2024-01-15T12:00:00")
```

### Using Context Manager

Automatically clean up the session when done:

```python
with SGDataClient() as client:
    weather = client.get_2hour_weather_forecast()
    temp = client.get_air_temperature()
```

### Handling Errors

```python
import requests

try:
    data = client.get_psi()
except requests.HTTPError as e:
    print(f"Oops, something went wrong: {e}")
```

### Custom Timeout

```python
# Need more time? Adjust the timeout
client = SGDataClient(timeout=60)
```

## API Details

All methods return parsed JSON as a dictionary. Most methods accept optional `date` or `date_time` parameters for historical data:

- `date` - Format: `"2024-01-15"`
- `date_time` - Format: `"2024-01-15T12:00:00"`

The client uses a 30-second timeout by default, which you can customize when creating it.

## Development

Want to contribute? Great!

```bash
git clone https://github.com/KT-afk/sgdata-sdk-python.git
cd sgdata-sdk-python
pip install -e ".[dev]"

# Run tests
pytest

# Check types
mypy sgdata

# Format code
black sgdata tests
```

## License

MIT

## Links

- Data source: [data.gov.sg](https://data.gov.sg)
- Issues and PRs welcome!
