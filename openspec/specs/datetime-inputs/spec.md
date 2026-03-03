## ADDED Requirements

### Requirement: Client methods accept datetime objects for temporal parameters
All `SGDataClient` methods that accept `date_time` or `date` parameters SHALL also accept Python `datetime` and `date` objects in addition to strings, formatting them internally before sending to the API.

#### Scenario: datetime object formatted as ISO 8601 string
- **WHEN** `client.get_psi(date_time=datetime(2024, 1, 15, 12, 0, 0))` is called
- **THEN** the API request SHALL include `date_time=2024-01-15T12:00:00` as a query parameter

#### Scenario: date object formatted as YYYY-MM-DD string
- **WHEN** `client.get_psi(date=date(2024, 1, 15))` is called
- **THEN** the API request SHALL include `date=2024-01-15` as a query parameter

#### Scenario: string passthrough unchanged
- **WHEN** `client.get_psi(date_time="2024-01-15T12:00:00")` is called with a string
- **THEN** the API request SHALL include `date_time=2024-01-15T12:00:00` unchanged

#### Scenario: None omitted from parameters
- **WHEN** `client.get_psi()` is called with no temporal parameters
- **THEN** the API request SHALL not include `date_time` or `date` query parameters

### Requirement: Invalid string raises ValueError
The SDK SHALL raise a `ValueError` (not an SDK exception) when an unparseable string is passed as a temporal parameter.

#### Scenario: Invalid date string raises ValueError
- **WHEN** `client.get_psi(date="not-a-date")` is called
- **THEN** a `ValueError` SHALL be raised before any HTTP request is made
