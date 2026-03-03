## ADDED Requirements

### Requirement: LotType enum encodes lot type codes
The SDK SHALL provide a `LotType` string enum with values: `CAR = "C"`, `MOTORCYCLE = "Y"`, `HEAVY_VEHICLE = "H"`, `SPECIAL = "S"`.

#### Scenario: LotType parses from API string
- **WHEN** the API returns `"lot_type": "C"` in a carpark_info object
- **THEN** the parsed `LotInfo.lot_type` SHALL equal `LotType.CAR`

#### Scenario: Unknown lot type raises validation error
- **WHEN** the API returns an unrecognised lot type code
- **THEN** Pydantic SHALL raise a `ValidationError`

### Requirement: LotInfo coerces string fields to correct types
The SDK SHALL provide a `LotInfo` model that automatically coerces `total_lots` and `lots_available` from strings to integers.

#### Scenario: String numbers coerced to int
- **WHEN** the API returns `"total_lots": "100"` and `"lots_available": "50"`
- **THEN** `LotInfo.total_lots` SHALL equal `100` (int) and `LotInfo.available_lots` SHALL equal `50` (int)

#### Scenario: Occupancy rate computed correctly
- **WHEN** `total_lots` is 100 and `available_lots` is 50
- **THEN** `LotInfo.occupancy_rate` SHALL equal `0.5` (float)

#### Scenario: Occupancy rate is zero when no total lots
- **WHEN** `total_lots` is 0
- **THEN** `LotInfo.occupancy_rate` SHALL equal `0.0` (no division error)

### Requirement: Carpark model provides convenience properties
The SDK SHALL provide a `Carpark` model with computed properties for common access patterns.

#### Scenario: car_lots returns C-type lot info
- **WHEN** a carpark has a `LotInfo` with `lot_type == LotType.CAR`
- **THEN** `Carpark.car_lots` SHALL return that `LotInfo` instance

#### Scenario: car_lots returns None when no car lots
- **WHEN** a carpark has no `LotInfo` with `lot_type == LotType.CAR`
- **THEN** `Carpark.car_lots` SHALL return `None`

#### Scenario: total_available sums across all lot types
- **WHEN** a carpark has car lots (50 available) and motorcycle lots (10 available)
- **THEN** `Carpark.total_available` SHALL equal `60`

#### Scenario: is_full is True when no lots available
- **WHEN** all `LotInfo` entries have `available_lots == 0`
- **THEN** `Carpark.is_full` SHALL be `True`

#### Scenario: Carpark update_datetime is a datetime object
- **WHEN** the API returns `"update_datetime": "2024-01-15T12:00:00"`
- **THEN** `Carpark.updated_at` SHALL be a `datetime` instance

### Requirement: CarparkAvailabilityResponse provides query methods
The SDK SHALL provide a `CarparkAvailabilityResponse` model with methods to filter and retrieve carparks.

#### Scenario: get returns carpark by number
- **WHEN** `response.get("HG1")` is called and carpark HG1 exists
- **THEN** it SHALL return the matching `Carpark` instance

#### Scenario: get returns None for unknown carpark
- **WHEN** `response.get("UNKNOWN")` is called
- **THEN** it SHALL return `None`

#### Scenario: available filters to carparks with spaces
- **WHEN** `response.available()` is called
- **THEN** it SHALL return only `Carpark` instances where `total_available > 0`

#### Scenario: available accepts lot_type filter
- **WHEN** `response.available(lot_type=LotType.CAR)` is called
- **THEN** it SHALL return only carparks with available car lots (where `car_lots.available_lots > 0`)

#### Scenario: full returns only full carparks
- **WHEN** `response.full()` is called
- **THEN** it SHALL return only `Carpark` instances where `is_full == True`

#### Scenario: response timestamp is a datetime object
- **WHEN** the API returns `"timestamp": "2026-03-03T15:58:36+08:00"`
- **THEN** `CarparkAvailabilityResponse.timestamp` SHALL be a `datetime` instance

#### Scenario: raw exposes original dict
- **WHEN** `response.raw` is accessed
- **THEN** it SHALL return the original parsed JSON dict unchanged
