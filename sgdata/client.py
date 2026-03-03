"""SGData SDK Client implementation."""

from datetime import date as date_type, datetime
from typing import Any, Dict, Optional, Union

import requests

from sgdata.exceptions import SGDataAPIError, SGDataError, SGDataTimeoutError, RateLimitError
from sgdata.models.carpark import CarparkAvailabilityResponse
from sgdata.models.air_quality import PSIResponse, PM25Response
from sgdata.models.weather import WeatherForecastResponse, StationReadingResponse


class SGDataClient:
    """Unified client for Singapore Government Data APIs.

    Provides access to 9 core endpoints covering weather, air quality, and carpark data.

    Args:
        base_url: Base URL for the API. Defaults to data.gov.sg API.
        timeout: Request timeout in seconds. Defaults to 30.
        retry: Enable automatic retry logic with exponential backoff. Requires tenacity.

    Example:
        >>> client = SGDataClient()
        >>> psi_data = client.get_psi()
        >>> historical_psi = client.get_psi(date_time="2024-01-15T12:00:00")
    """

    BASE_URL = "https://api.data.gov.sg/v1"

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: int = 30,
        retry: bool = False,
    ) -> None:
        """Initialize the SGData client.

        Args:
            base_url: Custom base URL for the API (optional).
            timeout: Request timeout in seconds.
            retry: Enable automatic retry with exponential backoff (requires tenacity).
        """
        self.base_url = base_url or self.BASE_URL
        self.timeout = timeout
        self.retry = retry
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "sgdata-sdk-python/0.2.0",
            "Accept": "application/json",
        })
        if retry:
            try:
                import tenacity  # noqa: F401
            except ImportError:
                raise ImportError(
                    "retry=True requires tenacity. Install it with: "
                    "pip install sgdata-sdk[retry]"
                )

    def _build_params(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> Dict[str, str]:
        """Build query parameters for API requests.

        Args:
            date_time: Datetime for historical data — accepts datetime object or ISO 8601 string.
            date: Date for historical data — accepts date/datetime object or YYYY-MM-DD string.

        Returns:
            Dictionary of query parameters with non-None values.
        """
        params: Dict[str, str] = {}
        if date_time is not None:
            if isinstance(date_time, datetime):
                params["date_time"] = date_time.isoformat()
            else:
                params["date_time"] = date_time
        if date is not None:
            if isinstance(date, datetime):
                params["date"] = date.strftime("%Y-%m-%d")
            elif isinstance(date, date_type):
                params["date"] = date.isoformat()
            else:
                params["date"] = date
        return params

    def _make_request(self, url: str, params: Optional[Dict[str, str]]) -> requests.Response:
        """Perform the raw HTTP GET call.

        Args:
            url: Full URL to request.
            params: Query parameters.

        Returns:
            The requests.Response object.

        Raises:
            SGDataTimeoutError: If the request times out.
            SGDataError: If a connection error occurs.
        """
        try:
            return self.session.get(url, params=params, timeout=self.timeout)
        except requests.Timeout as exc:
            raise SGDataTimeoutError(f"Request to {url} timed out") from exc
        except requests.ConnectionError as exc:
            raise SGDataError(f"Connection error: {exc}") from exc

    def _request(
        self,
        endpoint: str,
        params: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """Make HTTP GET request to the API.

        Args:
            endpoint: API endpoint path (e.g., "/environment/psi").
            params: Query parameters for the request.

        Returns:
            Parsed JSON response as a dictionary.

        Raises:
            SGDataTimeoutError: If the request times out.
            SGDataError: If a connection error occurs.
            RateLimitError: If the API returns HTTP 429.
            SGDataAPIError: If the API returns any other HTTP error.
        """
        url = f"{self.base_url}{endpoint}"

        if self.retry:
            import tenacity

            def _should_retry(exc: BaseException) -> bool:
                if isinstance(exc, SGDataTimeoutError):
                    return True
                if isinstance(exc, RateLimitError):
                    return True
                if isinstance(exc, SGDataAPIError) and exc.status_code in (500, 502, 503, 504):
                    return True
                return False

            for attempt in tenacity.Retrying(
                retry=tenacity.retry_if_exception(_should_retry),
                wait=tenacity.wait_exponential(multiplier=1, min=1, max=16),
                stop=tenacity.stop_after_attempt(3),
                reraise=True,
            ):
                with attempt:
                    response = self._make_request(url, params)
                    response = self._check_response(response, url)
        else:
            response = self._make_request(url, params)
            response = self._check_response(response, url)

        return response.json()  # type: ignore[no-any-return]

    def _check_response(
        self, response: requests.Response, url: str
    ) -> requests.Response:
        """Validate the HTTP response and raise SDK exceptions on errors.

        Args:
            response: The HTTP response object.
            url: The request URL (used in error messages).

        Returns:
            The same response object if no error.

        Raises:
            RateLimitError: On HTTP 429.
            SGDataAPIError: On other HTTP errors.
        """
        if response.status_code == 429:
            raise RateLimitError(f"Rate limited by API: {url}", response=response)

        try:
            response.raise_for_status()
        except requests.HTTPError as exc:
            raise SGDataAPIError(
                str(exc),
                status_code=response.status_code,
                response=response,
            ) from exc

        return response

    # Environment - Air Quality

    def get_psi(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> PSIResponse:
        """Get Pollutant Standards Index (PSI) readings.

        Returns hourly PSI readings across Singapore regions.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).
            date: Specific date for historical data (YYYY-MM-DD string or date/datetime).

        Returns:
            PSIResponse containing regional readings and timestamp.
        """
        params = self._build_params(date_time, date)
        raw = self._request("/environment/psi", params=params)
        return PSIResponse.from_dict(raw)

    def get_pm25(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> PM25Response:
        """Get PM2.5 (fine particulate matter) readings.

        Returns PM2.5 concentration levels across Singapore regions.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).
            date: Specific date for historical data (YYYY-MM-DD string or date/datetime).

        Returns:
            PM25Response containing regional readings and timestamp.
        """
        params = self._build_params(date_time, date)
        raw = self._request("/environment/pm25", params=params)
        return PM25Response.from_dict(raw)

    # Environment - Weather

    def get_2hour_weather_forecast(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> WeatherForecastResponse:
        """Get 2-hour weather forecast.

        Returns short-term weather forecasts for different areas of Singapore.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).
            date: Specific date for historical data (YYYY-MM-DD string or date/datetime).

        Returns:
            WeatherForecastResponse with area-specific predictions.
        """
        params = self._build_params(date_time, date)
        raw = self._request("/environment/2-hour-weather-forecast", params=params)
        return WeatherForecastResponse.from_dict(raw)

    def get_24hour_weather_forecast(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> WeatherForecastResponse:
        """Get 24-hour weather forecast.

        Returns general weather forecast for the next 24 hours.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).
            date: Specific date for historical data (YYYY-MM-DD string or date/datetime).

        Returns:
            WeatherForecastResponse including general conditions.
        """
        params = self._build_params(date_time, date)
        raw = self._request("/environment/24-hour-weather-forecast", params=params)
        return WeatherForecastResponse.from_dict(raw)

    def get_4day_weather_forecast(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> WeatherForecastResponse:
        """Get 4-day weather forecast.

        Returns extended weather forecast for the next 4 days.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).
            date: Specific date for historical data (YYYY-MM-DD string or date/datetime).

        Returns:
            WeatherForecastResponse with daily predictions.
        """
        params = self._build_params(date_time, date)
        raw = self._request("/environment/4-day-weather-forecast", params=params)
        return WeatherForecastResponse.from_dict(raw)

    def get_rainfall(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> StationReadingResponse:
        """Get rainfall measurements.

        Returns rainfall readings from weather stations across Singapore.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).
            date: Specific date for historical data (YYYY-MM-DD string or date/datetime).

        Returns:
            StationReadingResponse with rainfall data from multiple weather stations.
        """
        params = self._build_params(date_time, date)
        raw = self._request("/environment/rainfall", params=params)
        return StationReadingResponse.from_dict(raw)

    def get_relative_humidity(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> StationReadingResponse:
        """Get relative humidity readings.

        Returns humidity measurements from weather stations across Singapore.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).
            date: Specific date for historical data (YYYY-MM-DD string or date/datetime).

        Returns:
            StationReadingResponse with humidity data from multiple weather stations.
        """
        params = self._build_params(date_time, date)
        raw = self._request("/environment/relative-humidity", params=params)
        return StationReadingResponse.from_dict(raw)

    def get_air_temperature(
        self,
        date_time: Optional[Union[datetime, str]] = None,
        date: Optional[Union[date_type, str]] = None,
    ) -> StationReadingResponse:
        """Get air temperature readings.

        Returns temperature measurements from weather stations across Singapore.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).
            date: Specific date for historical data (YYYY-MM-DD string or date/datetime).

        Returns:
            StationReadingResponse with temperature data from multiple weather stations.
        """
        params = self._build_params(date_time, date)
        raw = self._request("/environment/air-temperature", params=params)
        return StationReadingResponse.from_dict(raw)

    # Transport - Carpark Availability

    def get_carpark_availability(
        self,
        date_time: Optional[Union[datetime, str]] = None,
    ) -> CarparkAvailabilityResponse:
        """Get carpark availability information.

        Returns real-time or historical carpark availability data for HDB carparks.
        Note: This endpoint only supports date_time parameter, not date.

        Args:
            date_time: Specific datetime for historical data (ISO 8601 string or datetime).

        Returns:
            CarparkAvailabilityResponse with lot counts and locations.
        """
        params = self._build_params(date_time, None)
        raw = self._request("/transport/carpark-availability", params=params)
        return CarparkAvailabilityResponse.from_dict(raw)

    def close(self) -> None:
        """Close the HTTP session.

        Should be called when done using the client to clean up resources.
        """
        self.session.close()

    def __enter__(self) -> "SGDataClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """Context manager exit."""
        self.close()
