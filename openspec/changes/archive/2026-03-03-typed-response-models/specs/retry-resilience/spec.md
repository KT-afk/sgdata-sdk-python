## ADDED Requirements

### Requirement: Client accepts retry configuration
The `SGDataClient` SHALL accept a `retry` boolean parameter (default `False`) that enables automatic retry on transient failures.

#### Scenario: Client created with retry enabled
- **WHEN** `SGDataClient(retry=True)` is called
- **THEN** subsequent requests SHALL automatically retry on transient failures

#### Scenario: Client created with default retry disabled
- **WHEN** `SGDataClient()` is called without `retry` parameter
- **THEN** requests SHALL NOT retry on failure (current behaviour preserved)

### Requirement: Retry requires tenacity optional dependency
When `retry=True` is used, the SDK SHALL require `tenacity` to be installed.

#### Scenario: retry=True without tenacity raises ImportError
- **WHEN** `SGDataClient(retry=True)` is called and `tenacity` is not installed
- **THEN** an `ImportError` SHALL be raised with a message instructing: `pip install sgdata-sdk[retry]`

### Requirement: Retry applies exponential backoff on transient errors
When retry is enabled, the SDK SHALL retry requests that fail with 429, 500, 502, 503, 504 or timeout, using exponential backoff with jitter.

#### Scenario: 500 response is retried up to 3 times
- **WHEN** retry is enabled and the API returns HTTP 500
- **THEN** the SDK SHALL retry the request up to 3 times before raising `SGDataAPIError`

#### Scenario: 429 response is retried after backoff
- **WHEN** retry is enabled and the API returns HTTP 429
- **THEN** the SDK SHALL retry with exponential backoff before raising `RateLimitError`

#### Scenario: 404 response is NOT retried
- **WHEN** retry is enabled and the API returns HTTP 404
- **THEN** the SDK SHALL raise `SGDataAPIError` immediately without retrying

#### Scenario: Successful response after retry returns data
- **WHEN** retry is enabled, first attempt returns 503, second returns 200
- **THEN** the SDK SHALL return the successful response without raising an exception
