## ADDED Requirements

### Requirement: SDK provides a base SGDataError exception
The SDK SHALL provide an `SGDataError` base exception class that all SDK-specific exceptions inherit from.

#### Scenario: SGDataError is catchable as a base type
- **WHEN** any SDK-specific exception is raised
- **THEN** it SHALL be catchable with `except SGDataError`

### Requirement: RateLimitError wraps 429 responses
The SDK SHALL raise `RateLimitError` (subclass of `SGDataError`) when the API returns HTTP 429.

#### Scenario: 429 response raises RateLimitError
- **WHEN** the API returns HTTP 429
- **THEN** `RateLimitError` SHALL be raised instead of a raw `requests.HTTPError`

#### Scenario: RateLimitError preserves original response
- **WHEN** `RateLimitError` is raised
- **THEN** the exception SHALL expose the original `requests.Response` via `.response`

### Requirement: SGDataTimeoutError wraps timeout exceptions
The SDK SHALL raise `SGDataTimeoutError` (subclass of `SGDataError`) when a request times out.

#### Scenario: Timeout raises SGDataTimeoutError
- **WHEN** the HTTP request exceeds the configured timeout
- **THEN** `SGDataTimeoutError` SHALL be raised instead of `requests.Timeout`

### Requirement: SGDataAPIError wraps non-429 HTTP errors
The SDK SHALL raise `SGDataAPIError` (subclass of `SGDataError`) for HTTP 4xx (except 429) and 5xx responses.

#### Scenario: 404 response raises SGDataAPIError
- **WHEN** the API returns HTTP 404
- **THEN** `SGDataAPIError` SHALL be raised with `.status_code == 404`

#### Scenario: 500 response raises SGDataAPIError
- **WHEN** the API returns HTTP 500
- **THEN** `SGDataAPIError` SHALL be raised with `.status_code == 500`
