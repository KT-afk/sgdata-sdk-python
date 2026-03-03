## ADDED Requirements

### Requirement: Region enum encodes Singapore regions
The SDK SHALL provide a `Region` string enum with values: `WEST = "west"`, `EAST = "east"`, `CENTRAL = "central"`, `SOUTH = "south"`, `NORTH = "north"`, `NATIONAL = "national"`.

#### Scenario: Region used as dict key in readings
- **WHEN** PSI readings are parsed
- **THEN** `PSIReading.psi_24h` SHALL be a `dict[Region, int]` keyed by `Region` enum values

### Requirement: PSIResponse provides typed air quality readings
The SDK SHALL provide a `PSIResponse` model returned by `SGDataClient.get_psi()`.

#### Scenario: PSIResponse contains typed readings
- **WHEN** `client.get_psi()` is called successfully
- **THEN** the returned `PSIResponse.readings` SHALL be a `PSIReading` instance with all pollutant metrics as typed fields

#### Scenario: PSIReading.psi_24h contains regional values
- **WHEN** the API returns psi_twenty_four_hourly data for all regions
- **THEN** `PSIReading.psi_24h[Region.NATIONAL]` SHALL return the national reading as an `int`

#### Scenario: PSIResponse timestamp is datetime
- **WHEN** the API returns a timestamp string
- **THEN** `PSIResponse.timestamp` SHALL be a `datetime` instance

#### Scenario: PSIResponse raw preserves original dict
- **WHEN** `response.raw` is accessed
- **THEN** it SHALL return the original parsed JSON dict

### Requirement: PM25Response provides typed PM2.5 readings
The SDK SHALL provide a `PM25Response` model returned by `SGDataClient.get_pm25()`.

#### Scenario: PM25Response contains regional pm25 hourly readings
- **WHEN** `client.get_pm25()` is called successfully
- **THEN** the returned `PM25Response.readings` SHALL contain `pm25_1h` as a `dict[Region, int]`

### Requirement: WeatherForecastResponse provides typed area forecasts
The SDK SHALL provide response models for the 2-hour, 24-hour, and 4-day weather forecast endpoints.

#### Scenario: AreaForecast includes geolocation from area_metadata
- **WHEN** the API returns area_metadata with coordinates
- **THEN** each `AreaForecast` SHALL include `latitude` and `longitude` merged from area_metadata

#### Scenario: get method retrieves forecast by area name
- **WHEN** `response.get("Ang Mo Kio")` is called
- **THEN** it SHALL return the matching `AreaForecast` instance

#### Scenario: get returns None for unknown area
- **WHEN** `response.get("Unknown Area")` is called
- **THEN** it SHALL return `None`

#### Scenario: valid_from and valid_to are datetime objects
- **WHEN** the API returns valid_period start and end strings
- **THEN** `response.valid_from` and `response.valid_to` SHALL be `datetime` instances

### Requirement: StationReadingResponse provides typed sensor data
The SDK SHALL provide a `StationReadingResponse` model for rainfall, humidity, and temperature endpoints.

#### Scenario: StationReading value is a float
- **WHEN** the API returns a sensor reading value
- **THEN** `StationReading.value` SHALL be a `float`

#### Scenario: StationReadingResponse readings is a list of StationReading
- **WHEN** `client.get_rainfall()` is called
- **THEN** the returned `StationReadingResponse.readings` SHALL be a `list[StationReading]`

#### Scenario: StationReading includes station geolocation
- **WHEN** the API returns station metadata with coordinates
- **THEN** each `StationReading` SHALL expose `latitude` and `longitude` as `float`
