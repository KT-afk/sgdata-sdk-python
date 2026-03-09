"""Comprehensive tests for SGDataClient."""

import builtins
from datetime import date, datetime
from typing import Any, Dict
from unittest.mock import Mock, patch, MagicMock
import pytest
import requests

from sgdata.client import SGDataClient
from sgdata.exceptions import SGDataAPIError, SGDataError, SGDataTimeoutError, RateLimitError
from sgdata.models.carpark import (
    CarparkAvailabilityResponse,
    Carpark,
    LotInfo,
    LotType,
)
from sgdata.models.air_quality import PSIResponse, PM25Response, Region
from sgdata.models.weather import WeatherForecastResponse, StationReadingResponse


# ---------------------------------------------------------------------------
# Minimal PSI response dict used across several tests
# ---------------------------------------------------------------------------
_MINIMAL_PSI_JSON: Dict[str, Any] = {
    "items": [
        {
            "timestamp": "2024-01-15T12:00:00+08:00",
            "update_timestamp": "2024-01-15T12:00:00+08:00",
            "readings": {
                "o3_sub_index": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "pm10_twenty_four_hourly": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "pm10_sub_index": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "co_sub_index": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "pm25_twenty_four_hourly": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "so2_sub_index": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "co_eight_hour_max": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "no2_one_hour_max": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "so2_twenty_four_hourly": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "pm25_sub_index": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "psi_twenty_four_hourly": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
                "o3_eight_hour_max": {"west": 1, "east": 1, "central": 1, "south": 1, "north": 1, "national": 1},
            },
        }
    ],
    "api_info": {"status": "healthy"},
}

# Minimal weather forecast JSON (2-hour style)
_MINIMAL_WEATHER_JSON: Dict[str, Any] = {
    "area_metadata": [
        {"name": "Ang Mo Kio", "label_location": {"latitude": 1.375, "longitude": 103.839}},
    ],
    "items": [
        {
            "timestamp": "2024-01-15T12:00:00+08:00",
            "valid_period": {
                "start": "2024-01-15T12:00:00+08:00",
                "end": "2024-01-15T14:00:00+08:00",
            },
            "forecasts": [
                {"area": "Ang Mo Kio", "forecast": "Partly Cloudy"},
            ],
        }
    ],
    "api_info": {"status": "healthy"},
}

# Minimal carpark JSON
_MINIMAL_CARPARK_JSON: Dict[str, Any] = {
    "items": [
        {
            "timestamp": "2024-01-15T12:00:00+08:00",
            "carpark_data": [
                {
                    "carpark_number": "HG1",
                    "update_datetime": "2024-01-15T12:00:00",
                    "carpark_info": [
                        {"total_lots": "100", "lot_type": "C", "lots_available": "50"}
                    ],
                }
            ],
        }
    ],
    "api_info": {"status": "healthy"},
}

# Minimal station reading JSON
_MINIMAL_STATION_JSON: Dict[str, Any] = {
    "metadata": {
        "stations": [
            {
                "id": "S104",
                "name": "Woodlands Ave 9",
                "location": {"latitude": 1.44387, "longitude": 103.786},
            }
        ]
    },
    "items": [
        {
            "timestamp": "2024-01-15T12:00:00+08:00",
            "readings": [{"station_id": "S104", "value": 25.4}],
        }
    ],
    "api_info": {"status": "healthy"},
}


def _make_mock_response(json_data: Dict[str, Any], status_code: int = 200) -> Mock:
    """Helper that builds a mock requests.Response returning *json_data*."""
    mock_resp = Mock()
    mock_resp.status_code = status_code
    mock_resp.json.return_value = json_data
    mock_resp.raise_for_status = Mock()
    return mock_resp


# ===========================================================================
# TestSGDataClientInitialization
# ===========================================================================


class TestSGDataClientInitialization:
    """Test client initialization and configuration."""

    def test_default_initialization(self):
        """Test client initializes with default base URL and timeout."""
        client = SGDataClient()

        assert client.base_url == "https://api.data.gov.sg/v1"
        assert client.timeout == 30
        assert isinstance(client.session, requests.Session)
        assert client.session.headers["User-Agent"] == "sgdata-sdk-python/0.2.1"
        assert client.session.headers["Accept"] == "application/json"
        client.close()

    def test_custom_base_url(self):
        """Test client initializes with custom base URL."""
        custom_url = "https://custom.api.example.com/v2"
        client = SGDataClient(base_url=custom_url)

        assert client.base_url == custom_url
        assert client.timeout == 30
        client.close()

    def test_custom_timeout(self):
        """Test client initializes with custom timeout."""
        client = SGDataClient(timeout=60)

        assert client.base_url == "https://api.data.gov.sg/v1"
        assert client.timeout == 60
        client.close()

    def test_custom_base_url_and_timeout(self):
        """Test client initializes with both custom base URL and timeout."""
        custom_url = "https://custom.api.example.com/v2"
        client = SGDataClient(base_url=custom_url, timeout=45)

        assert client.base_url == custom_url
        assert client.timeout == 45
        client.close()

    def test_retry_false_default(self):
        """Test that retry defaults to False."""
        client = SGDataClient()
        assert client.retry is False
        client.close()

    def test_retry_true_without_tenacity(self):
        """Test that retry=True raises ImportError when tenacity is not installed."""
        real_import = builtins.__import__

        def mock_import(name, *args, **kwargs):
            if name == "tenacity":
                raise ImportError("No module named 'tenacity'")
            return real_import(name, *args, **kwargs)

        with patch("builtins.__import__", side_effect=mock_import):
            with pytest.raises(ImportError, match="tenacity"):
                SGDataClient(retry=True)


# ===========================================================================
# TestParameterBuilding
# ===========================================================================


class TestParameterBuilding:
    """Test query parameter building logic."""

    def test_build_params_no_parameters(self):
        """Test building params with no date or date_time."""
        client = SGDataClient()
        params = client._build_params()

        assert params == {}
        client.close()

    def test_build_params_with_date_time_only(self):
        """Test building params with date_time string parameter."""
        client = SGDataClient()
        params = client._build_params(date_time="2024-01-15T12:00:00")

        assert params == {"date_time": "2024-01-15T12:00:00"}
        client.close()

    def test_build_params_with_date_only(self):
        """Test building params with date string parameter."""
        client = SGDataClient()
        params = client._build_params(date="2024-01-15")

        assert params == {"date": "2024-01-15"}
        client.close()

    def test_build_params_with_both_parameters(self):
        """Test building params with both date_time and date strings."""
        client = SGDataClient()
        params = client._build_params(
            date_time="2024-01-15T12:00:00",
            date="2024-01-15",
        )

        assert params == {
            "date_time": "2024-01-15T12:00:00",
            "date": "2024-01-15",
        }
        client.close()

    def test_build_params_with_datetime_object(self):
        """Test building params with a datetime object."""
        client = SGDataClient()
        dt = datetime(2024, 1, 15, 12, 0, 0)
        params = client._build_params(date_time=dt)

        assert params == {"date_time": "2024-01-15T12:00:00"}
        client.close()

    def test_build_params_with_date_object(self):
        """Test building params with a date object."""
        client = SGDataClient()
        d = date(2024, 1, 15)
        params = client._build_params(date=d)

        assert params == {"date": "2024-01-15"}
        client.close()


# ===========================================================================
# TestHTTPRequests
# ===========================================================================


class TestHTTPRequests:
    """Test HTTP request handling."""

    @patch("requests.Session.get")
    def test_successful_request(self, mock_get):
        """Test successful API request returns parsed JSON dict."""
        mock_response = _make_mock_response({"data": "test"})
        mock_get.return_value = mock_response

        client = SGDataClient()
        result = client._request("/test/endpoint")

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/test/endpoint",
            params=None,
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_request_with_params(self, mock_get):
        """Test API request with query parameters."""
        mock_response = _make_mock_response({"data": "test"})
        mock_get.return_value = mock_response

        client = SGDataClient()
        params = {"date_time": "2024-01-15T12:00:00"}
        result = client._request("/test/endpoint", params=params)

        assert result == {"data": "test"}
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/test/endpoint",
            params=params,
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_request_http_error_4xx(self, mock_get):
        """Test API request with 4xx HTTP error raises SGDataAPIError."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
        mock_get.return_value = mock_response

        client = SGDataClient()

        with pytest.raises(SGDataAPIError):
            client._request("/test/endpoint")

        client.close()

    @patch("requests.Session.get")
    def test_request_http_error_5xx(self, mock_get):
        """Test API request with 5xx HTTP error raises SGDataAPIError with status code."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Internal Server Error")
        mock_get.return_value = mock_response

        client = SGDataClient()

        with pytest.raises(SGDataAPIError) as exc_info:
            client._request("/test/endpoint")

        assert exc_info.value.status_code == 500
        client.close()

    @patch("requests.Session.get")
    def test_request_timeout(self, mock_get):
        """Test API request timeout raises SGDataTimeoutError."""
        mock_get.side_effect = requests.Timeout("Request timed out")

        client = SGDataClient()

        with pytest.raises(SGDataTimeoutError):
            client._request("/test/endpoint")

        client.close()

    @patch("requests.Session.get")
    def test_request_connection_error(self, mock_get):
        """Test API request connection error raises SGDataError."""
        mock_get.side_effect = requests.ConnectionError("Connection failed")

        client = SGDataClient()

        with pytest.raises(SGDataError):
            client._request("/test/endpoint")

        client.close()

    @patch("requests.Session.get")
    def test_request_rate_limit(self, mock_get):
        """Test HTTP 429 response raises RateLimitError."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        client = SGDataClient()

        with pytest.raises(RateLimitError):
            client._request("/test/endpoint")

        client.close()

    @patch("requests.Session.get")
    def test_request_rate_limit_has_response(self, mock_get):
        """Test RateLimitError carries the response object."""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.return_value = mock_response

        client = SGDataClient()

        with pytest.raises(RateLimitError) as exc_info:
            client._request("/test/endpoint")

        assert exc_info.value.response is mock_response
        client.close()


# ===========================================================================
# TestAirQualityEndpoints
# ===========================================================================


class TestAirQualityEndpoints:
    """Test air quality API endpoints."""

    @patch("requests.Session.get")
    def test_get_psi_current(self, mock_get, sample_psi_data):
        """Test getting current PSI data returns PSIResponse."""
        mock_get.return_value = _make_mock_response(sample_psi_data)

        client = SGDataClient()
        result = client.get_psi()

        assert isinstance(result, PSIResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/psi",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_psi_with_date_time(self, mock_get, sample_psi_data):
        """Test getting historical PSI data with date_time returns PSIResponse."""
        mock_get.return_value = _make_mock_response(sample_psi_data)

        client = SGDataClient()
        result = client.get_psi(date_time="2024-01-15T12:00:00")

        assert isinstance(result, PSIResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/psi",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_psi_with_date(self, mock_get, sample_psi_data):
        """Test getting historical PSI data with date returns PSIResponse."""
        mock_get.return_value = _make_mock_response(sample_psi_data)

        client = SGDataClient()
        result = client.get_psi(date="2024-01-15")

        assert isinstance(result, PSIResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/psi",
            params={"date": "2024-01-15"},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_pm25_current(self, mock_get):
        """Test getting current PM2.5 data returns PM25Response."""
        pm25_data = {
            "items": [
                {
                    "timestamp": "2024-01-15T12:00:00+08:00",
                    "readings": {
                        "pm25_one_hourly": {
                            "west": 10,
                            "east": 12,
                            "central": 11,
                            "south": 9,
                            "north": 13,
                            "national": 11,
                        }
                    },
                }
            ],
            "api_info": {"status": "healthy"},
        }
        mock_get.return_value = _make_mock_response(pm25_data)

        client = SGDataClient()
        result = client.get_pm25()

        assert isinstance(result, PM25Response)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/pm25",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_pm25_with_date_time(self, mock_get):
        """Test getting historical PM2.5 data with date_time returns PM25Response."""
        pm25_data = {
            "items": [
                {
                    "timestamp": "2024-01-15T12:00:00+08:00",
                    "readings": {
                        "pm25_one_hourly": {
                            "west": 10,
                            "east": 12,
                            "central": 11,
                            "south": 9,
                            "north": 13,
                            "national": 11,
                        }
                    },
                }
            ],
            "api_info": {"status": "healthy"},
        }
        mock_get.return_value = _make_mock_response(pm25_data)

        client = SGDataClient()
        result = client.get_pm25(date_time="2024-01-15T12:00:00")

        assert isinstance(result, PM25Response)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/pm25",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_pm25_with_date(self, mock_get):
        """Test getting historical PM2.5 data with date returns PM25Response."""
        pm25_data = {
            "items": [
                {
                    "timestamp": "2024-01-15T12:00:00+08:00",
                    "readings": {
                        "pm25_one_hourly": {
                            "west": 10,
                            "east": 12,
                            "central": 11,
                            "south": 9,
                            "north": 13,
                            "national": 11,
                        }
                    },
                }
            ],
            "api_info": {"status": "healthy"},
        }
        mock_get.return_value = _make_mock_response(pm25_data)

        client = SGDataClient()
        result = client.get_pm25(date="2024-01-15")

        assert isinstance(result, PM25Response)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/pm25",
            params={"date": "2024-01-15"},
            timeout=30,
        )
        client.close()


# ===========================================================================
# TestWeatherForecastEndpoints
# ===========================================================================


class TestWeatherForecastEndpoints:
    """Test weather forecast API endpoints."""

    @patch("requests.Session.get")
    def test_get_2hour_weather_forecast_current(self, mock_get, sample_weather_forecast_data):
        """Test getting current 2-hour weather forecast returns WeatherForecastResponse."""
        mock_get.return_value = _make_mock_response(sample_weather_forecast_data)

        client = SGDataClient()
        result = client.get_2hour_weather_forecast()

        assert isinstance(result, WeatherForecastResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_2hour_weather_forecast_with_date_time(self, mock_get, sample_weather_forecast_data):
        """Test getting historical 2-hour weather forecast with date_time."""
        mock_get.return_value = _make_mock_response(sample_weather_forecast_data)

        client = SGDataClient()
        result = client.get_2hour_weather_forecast(date_time="2024-01-15T12:00:00")

        assert isinstance(result, WeatherForecastResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/2-hour-weather-forecast",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_24hour_weather_forecast_current(self, mock_get, sample_weather_forecast_data):
        """Test getting current 24-hour weather forecast returns WeatherForecastResponse."""
        mock_get.return_value = _make_mock_response(sample_weather_forecast_data)

        client = SGDataClient()
        result = client.get_24hour_weather_forecast()

        assert isinstance(result, WeatherForecastResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_24hour_weather_forecast_with_date_time(self, mock_get, sample_weather_forecast_data):
        """Test getting historical 24-hour weather forecast with date_time."""
        mock_get.return_value = _make_mock_response(sample_weather_forecast_data)

        client = SGDataClient()
        result = client.get_24hour_weather_forecast(date_time="2024-01-15T12:00:00")

        assert isinstance(result, WeatherForecastResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/24-hour-weather-forecast",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_4day_weather_forecast_current(self, mock_get, sample_weather_forecast_data):
        """Test getting current 4-day weather forecast returns WeatherForecastResponse."""
        mock_get.return_value = _make_mock_response(sample_weather_forecast_data)

        client = SGDataClient()
        result = client.get_4day_weather_forecast()

        assert isinstance(result, WeatherForecastResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/4-day-weather-forecast",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_4day_weather_forecast_with_date_time(self, mock_get, sample_weather_forecast_data):
        """Test getting historical 4-day weather forecast with date_time."""
        mock_get.return_value = _make_mock_response(sample_weather_forecast_data)

        client = SGDataClient()
        result = client.get_4day_weather_forecast(date_time="2024-01-15T12:00:00")

        assert isinstance(result, WeatherForecastResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/4-day-weather-forecast",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()


# ===========================================================================
# TestWeatherMeasurementEndpoints
# ===========================================================================


class TestWeatherMeasurementEndpoints:
    """Test weather measurement API endpoints."""

    @patch("requests.Session.get")
    def test_get_rainfall_current(self, mock_get):
        """Test getting current rainfall data returns StationReadingResponse."""
        mock_get.return_value = _make_mock_response(_MINIMAL_STATION_JSON)

        client = SGDataClient()
        result = client.get_rainfall()

        assert isinstance(result, StationReadingResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/rainfall",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_rainfall_with_date_time(self, mock_get):
        """Test getting historical rainfall data with date_time."""
        mock_get.return_value = _make_mock_response(_MINIMAL_STATION_JSON)

        client = SGDataClient()
        result = client.get_rainfall(date_time="2024-01-15T12:00:00")

        assert isinstance(result, StationReadingResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/rainfall",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_relative_humidity_current(self, mock_get):
        """Test getting current relative humidity data returns StationReadingResponse."""
        mock_get.return_value = _make_mock_response(_MINIMAL_STATION_JSON)

        client = SGDataClient()
        result = client.get_relative_humidity()

        assert isinstance(result, StationReadingResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/relative-humidity",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_relative_humidity_with_date_time(self, mock_get):
        """Test getting historical relative humidity data with date_time."""
        mock_get.return_value = _make_mock_response(_MINIMAL_STATION_JSON)

        client = SGDataClient()
        result = client.get_relative_humidity(date_time="2024-01-15T12:00:00")

        assert isinstance(result, StationReadingResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/relative-humidity",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_air_temperature_current(self, mock_get):
        """Test getting current air temperature data returns StationReadingResponse."""
        mock_get.return_value = _make_mock_response(_MINIMAL_STATION_JSON)

        client = SGDataClient()
        result = client.get_air_temperature()

        assert isinstance(result, StationReadingResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/air-temperature",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_air_temperature_with_date_time(self, mock_get):
        """Test getting historical air temperature data with date_time."""
        mock_get.return_value = _make_mock_response(_MINIMAL_STATION_JSON)

        client = SGDataClient()
        result = client.get_air_temperature(date_time="2024-01-15T12:00:00")

        assert isinstance(result, StationReadingResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/environment/air-temperature",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()


# ===========================================================================
# TestTransportEndpoints
# ===========================================================================


class TestTransportEndpoints:
    """Test transport API endpoints."""

    @patch("requests.Session.get")
    def test_get_carpark_availability_current(self, mock_get, sample_carpark_data):
        """Test getting current carpark availability returns CarparkAvailabilityResponse."""
        mock_get.return_value = _make_mock_response(sample_carpark_data)

        client = SGDataClient()
        result = client.get_carpark_availability()

        assert isinstance(result, CarparkAvailabilityResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/transport/carpark-availability",
            params={},
            timeout=30,
        )
        client.close()

    @patch("requests.Session.get")
    def test_get_carpark_availability_with_date_time(self, mock_get, sample_carpark_data):
        """Test getting historical carpark availability with date_time."""
        mock_get.return_value = _make_mock_response(sample_carpark_data)

        client = SGDataClient()
        result = client.get_carpark_availability(date_time="2024-01-15T12:00:00")

        assert isinstance(result, CarparkAvailabilityResponse)
        mock_get.assert_called_once_with(
            "https://api.data.gov.sg/v1/transport/carpark-availability",
            params={"date_time": "2024-01-15T12:00:00"},
            timeout=30,
        )
        client.close()


# ===========================================================================
# TestSessionManagement
# ===========================================================================


class TestSessionManagement:
    """Test session management and cleanup."""

    def test_close_session(self):
        """Test that close() properly closes the session."""
        client = SGDataClient()
        session = client.session

        client.close()

        assert session is not None

    def test_context_manager_entry(self):
        """Test context manager __enter__ returns self."""
        client = SGDataClient()

        with client as ctx_client:
            assert ctx_client is client
            assert isinstance(ctx_client.session, requests.Session)

    def test_context_manager_exit(self):
        """Test context manager __exit__ closes session."""
        with SGDataClient() as client:
            session = client.session
            assert isinstance(session, requests.Session)

        assert session is not None

    @patch("requests.Session.get")
    def test_context_manager_with_request(self, mock_get, sample_psi_data):
        """Test using client within context manager."""
        mock_get.return_value = _make_mock_response(sample_psi_data)

        with SGDataClient() as client:
            result = client.get_psi()
            assert isinstance(result, PSIResponse)

        mock_get.assert_called_once()


# ===========================================================================
# TestCarparkModels
# ===========================================================================


class TestCarparkModels:
    """Unit tests for carpark model classes."""

    def _make_lot(self, total: str, available: str, lot_type: str = "C") -> LotInfo:
        return LotInfo._from_api({
            "total_lots": total,
            "lots_available": available,
            "lot_type": lot_type,
        })

    def _make_carpark(self, lots: list) -> Carpark:
        return Carpark(
            carpark_number="TEST",
            updated_at=datetime(2024, 1, 15, 12, 0, 0),
            lots=lots,
        )

    def test_lot_info_coerces_string_numbers(self):
        """LotInfo._from_api coerces string numbers to int."""
        lot = self._make_lot("100", "50", "C")
        assert lot.total_lots == 100
        assert lot.available_lots == 50
        assert isinstance(lot.total_lots, int)
        assert isinstance(lot.available_lots, int)

    def test_lot_info_occupancy_rate(self):
        """LotInfo.occupancy_rate computes available / total."""
        lot = self._make_lot("100", "50")
        assert lot.occupancy_rate == 0.5

    def test_lot_info_occupancy_rate_zero_total(self):
        """LotInfo.occupancy_rate returns 0.0 when total_lots is 0 (no ZeroDivisionError)."""
        lot = self._make_lot("0", "0")
        assert lot.occupancy_rate == 0.0

    def test_lot_info_lot_type_enum(self):
        """LotInfo.lot_type is coerced to the LotType enum."""
        lot = self._make_lot("100", "50", "C")
        assert lot.lot_type == LotType.CAR

    def test_carpark_car_lots_returns_c_type(self):
        """car_lots returns the C-type lot when present."""
        lot_c = self._make_lot("100", "50", "C")
        lot_y = self._make_lot("20", "10", "Y")
        carpark = self._make_carpark([lot_c, lot_y])
        assert carpark.car_lots is lot_c

    def test_carpark_car_lots_returns_none(self):
        """car_lots returns None when no C-type lot exists."""
        lot_y = self._make_lot("20", "10", "Y")
        carpark = self._make_carpark([lot_y])
        assert carpark.car_lots is None

    def test_carpark_total_available(self):
        """total_available sums available_lots across all lot types."""
        lot_c = self._make_lot("100", "50", "C")
        lot_y = self._make_lot("20", "10", "Y")
        carpark = self._make_carpark([lot_c, lot_y])
        assert carpark.total_available == 60

    def test_carpark_is_full_when_no_lots(self):
        """is_full returns True when all available_lots are 0."""
        lot_c = self._make_lot("100", "0", "C")
        lot_y = self._make_lot("20", "0", "Y")
        carpark = self._make_carpark([lot_c, lot_y])
        assert carpark.is_full is True

    def test_carpark_is_full_false_when_has_lots(self):
        """is_full returns False when at least one lot is available."""
        lot_c = self._make_lot("100", "50", "C")
        lot_y = self._make_lot("20", "0", "Y")
        carpark = self._make_carpark([lot_c, lot_y])
        assert carpark.is_full is False


# ===========================================================================
# TestCarparkAvailabilityResponse
# ===========================================================================


class TestCarparkAvailabilityResponse:
    """Integration-style tests for CarparkAvailabilityResponse using fixture data."""

    def test_from_dict_parses_carparks(self, sample_carpark_data):
        """from_dict produces a non-empty list of Carpark objects."""
        response = CarparkAvailabilityResponse.from_dict(sample_carpark_data)
        assert len(response.carparks) > 0
        assert all(isinstance(c, Carpark) for c in response.carparks)

    def test_from_dict_timestamp_is_datetime(self, sample_carpark_data):
        """from_dict parses timestamp to a datetime instance."""
        response = CarparkAvailabilityResponse.from_dict(sample_carpark_data)
        assert isinstance(response.timestamp, datetime)

    def test_get_returns_carpark(self, sample_carpark_data):
        """get() returns the matching Carpark by number."""
        response = CarparkAvailabilityResponse.from_dict(sample_carpark_data)
        carpark = response.get("HG1")
        assert carpark is not None
        assert carpark.carpark_number == "HG1"

    def test_get_returns_none_for_unknown(self, sample_carpark_data):
        """get() returns None for an unknown carpark number."""
        response = CarparkAvailabilityResponse.from_dict(sample_carpark_data)
        assert response.get("UNKNOWN") is None

    def test_available_returns_carparks_with_lots(self, sample_carpark_data):
        """available() returns only carparks with total_available > 0."""
        response = CarparkAvailabilityResponse.from_dict(sample_carpark_data)
        available = response.available()
        assert all(c.total_available > 0 for c in available)

    def test_full_returns_full_carparks(self):
        """full() returns carparks where every lot type is at capacity."""
        full_data = {
            "items": [
                {
                    "timestamp": "2024-01-15T12:00:00+08:00",
                    "carpark_data": [
                        {
                            "carpark_number": "FULL1",
                            "update_datetime": "2024-01-15T12:00:00",
                            "carpark_info": [
                                {"total_lots": "50", "lot_type": "C", "lots_available": "0"}
                            ],
                        },
                        {
                            "carpark_number": "PARTIAL1",
                            "update_datetime": "2024-01-15T12:00:00",
                            "carpark_info": [
                                {"total_lots": "50", "lot_type": "C", "lots_available": "10"}
                            ],
                        },
                    ],
                }
            ]
        }
        response = CarparkAvailabilityResponse.from_dict(full_data)
        full_list = response.full()
        assert len(full_list) == 1
        assert full_list[0].carpark_number == "FULL1"

    def test_raw_preserves_original_dict(self, sample_carpark_data):
        """raw attribute preserves the original API response dict."""
        response = CarparkAvailabilityResponse.from_dict(sample_carpark_data)
        assert response.raw == sample_carpark_data


# ===========================================================================
# TestPSIResponse
# ===========================================================================


class TestPSIResponse:
    """Tests for PSIResponse parsing using the sample_psi_data fixture."""

    def test_from_dict_returns_psi_response(self, sample_psi_data):
        """from_dict returns a PSIResponse instance."""
        response = PSIResponse.from_dict(sample_psi_data)
        assert isinstance(response, PSIResponse)

    def test_timestamp_is_datetime(self, sample_psi_data):
        """timestamp field is a datetime instance."""
        response = PSIResponse.from_dict(sample_psi_data)
        assert isinstance(response.timestamp, datetime)

    def test_psi_24h_alias(self, sample_psi_data):
        """psi_24h property is an alias for psi_twenty_four_hourly."""
        response = PSIResponse.from_dict(sample_psi_data)
        assert response.readings.psi_24h is response.readings.psi_twenty_four_hourly

    def test_national_reading_accessible(self, sample_psi_data):
        """psi_24h national reading matches the fixture value of 62."""
        response = PSIResponse.from_dict(sample_psi_data)
        assert response.readings.psi_24h[Region.NATIONAL] == 58

    def test_raw_preserves_original(self, sample_psi_data):
        """raw attribute preserves the original API response dict."""
        response = PSIResponse.from_dict(sample_psi_data)
        assert response.raw == sample_psi_data

    def test_all_regions_present(self, sample_psi_data):
        """All six regions are present in the psi_24h dict."""
        response = PSIResponse.from_dict(sample_psi_data)
        regions = set(response.readings.psi_24h.keys())
        assert Region.NATIONAL in regions
        assert Region.WEST in regions
        assert Region.EAST in regions
        assert Region.CENTRAL in regions
        assert Region.SOUTH in regions
        assert Region.NORTH in regions


# ===========================================================================
# TestWeatherForecastResponse
# ===========================================================================


class TestWeatherForecastResponse:
    """Tests for WeatherForecastResponse parsing using the fixture data."""

    def test_from_dict_returns_response(self, sample_weather_forecast_data):
        """from_dict returns a WeatherForecastResponse instance."""
        response = WeatherForecastResponse.from_dict(sample_weather_forecast_data)
        assert isinstance(response, WeatherForecastResponse)

    def test_forecasts_have_coordinates(self, sample_weather_forecast_data):
        """AreaForecast entries have latitude and longitude from area_metadata."""
        response = WeatherForecastResponse.from_dict(sample_weather_forecast_data)
        for forecast in response.forecasts:
            # Coordinates should be non-zero (populated from area_metadata)
            assert forecast.latitude != 0.0 or forecast.longitude != 0.0

    def test_ang_mo_kio_coordinates(self, sample_weather_forecast_data):
        """Ang Mo Kio forecast has correct coordinates merged from area_metadata."""
        response = WeatherForecastResponse.from_dict(sample_weather_forecast_data)
        amk = response.get("Ang Mo Kio")
        assert amk is not None
        assert amk.latitude == pytest.approx(1.375)
        assert amk.longitude == pytest.approx(103.839)

    def test_get_by_area_name(self, sample_weather_forecast_data):
        """get() returns the AreaForecast matching the given area name."""
        response = WeatherForecastResponse.from_dict(sample_weather_forecast_data)
        forecast = response.get("Ang Mo Kio")
        assert forecast is not None
        assert forecast.area == "Ang Mo Kio"

    def test_get_returns_none_for_unknown(self, sample_weather_forecast_data):
        """get() returns None for an unknown area name."""
        response = WeatherForecastResponse.from_dict(sample_weather_forecast_data)
        assert response.get("Atlantis") is None

    def test_valid_from_is_datetime(self, sample_weather_forecast_data):
        """valid_from is a datetime instance."""
        response = WeatherForecastResponse.from_dict(sample_weather_forecast_data)
        assert isinstance(response.valid_from, datetime)

    def test_raw_preserves_original(self, sample_weather_forecast_data):
        """raw attribute preserves the original API response dict."""
        response = WeatherForecastResponse.from_dict(sample_weather_forecast_data)
        assert response.raw == sample_weather_forecast_data


# ===========================================================================
# TestDatetimeInputs
# ===========================================================================


class TestDatetimeInputs:
    """Test that datetime/date/str inputs to endpoint methods produce correct params."""

    @patch("requests.Session.get")
    def test_datetime_object_formatted_correctly(self, mock_get):
        """A datetime object is formatted as ISO 8601 string in params."""
        mock_get.return_value = _make_mock_response(_MINIMAL_PSI_JSON)

        client = SGDataClient()
        client.get_psi(date_time=datetime(2024, 1, 15, 12, 0, 0))

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"date_time": "2024-01-15T12:00:00"}
        client.close()

    @patch("requests.Session.get")
    def test_date_object_formatted_correctly(self, mock_get):
        """A date object is formatted as YYYY-MM-DD string in params."""
        mock_get.return_value = _make_mock_response(_MINIMAL_PSI_JSON)

        client = SGDataClient()
        client.get_psi(date=date(2024, 1, 15))

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"date": "2024-01-15"}
        client.close()

    @patch("requests.Session.get")
    def test_string_passed_through(self, mock_get):
        """A string date_time is passed through unchanged."""
        mock_get.return_value = _make_mock_response(_MINIMAL_PSI_JSON)

        client = SGDataClient()
        client.get_psi(date_time="2024-01-15T12:00:00")

        _, kwargs = mock_get.call_args
        assert kwargs["params"] == {"date_time": "2024-01-15T12:00:00"}
        client.close()

    def test_date_param_with_datetime_object(self):
        """A datetime passed to the date param is formatted as YYYY-MM-DD."""
        client = SGDataClient()
        params = client._build_params(date=datetime(2024, 1, 15, 14, 30, 0))
        assert params == {"date": "2024-01-15"}
        client.close()


# ===========================================================================
# TestApiKeySupport
# ===========================================================================


class TestApiKeySupport:
    """Test API key header support."""

    def test_api_key_sets_header(self):
        """api_key parameter sets the api-key header on the session."""
        client = SGDataClient(api_key="test-key-123")
        assert client.session.headers["api-key"] == "test-key-123"
        client.close()

    def test_no_api_key_by_default(self):
        """No api-key header is set when api_key is not provided."""
        client = SGDataClient()
        assert "api-key" not in client.session.headers
        client.close()

    @patch("requests.Session.get")
    def test_api_key_sent_with_request(self, mock_get):
        """api-key header is sent with every request."""
        mock_get.return_value = _make_mock_response(_MINIMAL_PSI_JSON)

        client = SGDataClient(api_key="my-secret-key")
        client.get_psi()

        assert client.session.headers["api-key"] == "my-secret-key"
        client.close()


# ===========================================================================
# TestRetryBehavior
# ===========================================================================


class TestRetryBehavior:
    """Test retry logic with tenacity."""

    @patch("requests.Session.get")
    def test_retry_succeeds_after_transient_failure(self, mock_get):
        """Retry recovers from a transient 500 error."""
        fail_resp = Mock()
        fail_resp.status_code = 500
        fail_resp.raise_for_status.side_effect = requests.HTTPError("500")

        ok_resp = _make_mock_response(_MINIMAL_PSI_JSON)

        mock_get.side_effect = [fail_resp, ok_resp]

        client = SGDataClient(retry=True)
        result = client.get_psi()

        assert isinstance(result, PSIResponse)
        assert mock_get.call_count == 2
        client.close()

    @patch("requests.Session.get")
    def test_retry_on_rate_limit(self, mock_get):
        """Retry recovers from a 429 rate limit."""
        rate_resp = Mock()
        rate_resp.status_code = 429

        ok_resp = _make_mock_response(_MINIMAL_PSI_JSON)

        mock_get.side_effect = [rate_resp, ok_resp]

        client = SGDataClient(retry=True)
        result = client.get_psi()

        assert isinstance(result, PSIResponse)
        assert mock_get.call_count == 2
        client.close()

    @patch("requests.Session.get")
    def test_retry_on_timeout(self, mock_get):
        """Retry recovers from a timeout."""
        ok_resp = _make_mock_response(_MINIMAL_PSI_JSON)
        mock_get.side_effect = [requests.Timeout("timed out"), ok_resp]

        client = SGDataClient(retry=True)
        result = client.get_psi()

        assert isinstance(result, PSIResponse)
        assert mock_get.call_count == 2
        client.close()

    @patch("requests.Session.get")
    def test_retry_does_not_retry_4xx(self, mock_get):
        """Retry does NOT retry on a 404 client error."""
        fail_resp = Mock()
        fail_resp.status_code = 404
        fail_resp.raise_for_status.side_effect = requests.HTTPError("404")
        mock_get.return_value = fail_resp

        client = SGDataClient(retry=True)

        with pytest.raises(SGDataAPIError):
            client.get_psi()

        assert mock_get.call_count == 1
        client.close()

    @patch("requests.Session.get")
    def test_retry_exhausted_raises(self, mock_get):
        """After 3 failed attempts, the exception is re-raised."""
        fail_resp = Mock()
        fail_resp.status_code = 502
        fail_resp.raise_for_status.side_effect = requests.HTTPError("502")
        mock_get.return_value = fail_resp

        client = SGDataClient(retry=True)

        with pytest.raises(SGDataAPIError) as exc_info:
            client.get_psi()

        assert exc_info.value.status_code == 502
        assert mock_get.call_count == 3
        client.close()


# ===========================================================================
# TestPSIReadingAliases
# ===========================================================================


class TestPSIReadingAliases:
    """Test all PSIReading property aliases."""

    def test_pm25_24h_alias(self, sample_psi_data):
        """pm25_24h is an alias for pm25_twenty_four_hourly."""
        response = PSIResponse.from_dict(sample_psi_data)
        assert response.readings.pm25_24h is response.readings.pm25_twenty_four_hourly

    def test_pm10_24h_alias(self, sample_psi_data):
        """pm10_24h is an alias for pm10_twenty_four_hourly."""
        response = PSIResponse.from_dict(sample_psi_data)
        assert response.readings.pm10_24h is response.readings.pm10_twenty_four_hourly


# ===========================================================================
# TestAvailableWithNonCarLotType
# ===========================================================================


class TestAvailableWithNonCarLotType:
    """Test available() filtering with non-CAR lot types."""

    def test_available_motorcycle_lots(self):
        """available(LotType.MOTORCYCLE) filters by Y-type lots."""
        data = {
            "items": [
                {
                    "timestamp": "2024-01-15T12:00:00+08:00",
                    "carpark_data": [
                        {
                            "carpark_number": "HAS_Y",
                            "update_datetime": "2024-01-15T12:00:00",
                            "carpark_info": [
                                {"total_lots": "10", "lot_type": "Y", "lots_available": "5"},
                                {"total_lots": "50", "lot_type": "C", "lots_available": "0"},
                            ],
                        },
                        {
                            "carpark_number": "NO_Y",
                            "update_datetime": "2024-01-15T12:00:00",
                            "carpark_info": [
                                {"total_lots": "50", "lot_type": "C", "lots_available": "20"},
                            ],
                        },
                        {
                            "carpark_number": "EMPTY_Y",
                            "update_datetime": "2024-01-15T12:00:00",
                            "carpark_info": [
                                {"total_lots": "10", "lot_type": "Y", "lots_available": "0"},
                            ],
                        },
                    ],
                }
            ]
        }
        response = CarparkAvailabilityResponse.from_dict(data)
        available = response.available(lot_type=LotType.MOTORCYCLE)
        assert len(available) == 1
        assert available[0].carpark_number == "HAS_Y"

    def test_available_heavy_vehicle_lots(self):
        """available(LotType.HEAVY_VEHICLE) filters by H-type lots."""
        data = {
            "items": [
                {
                    "timestamp": "2024-01-15T12:00:00+08:00",
                    "carpark_data": [
                        {
                            "carpark_number": "HAS_H",
                            "update_datetime": "2024-01-15T12:00:00",
                            "carpark_info": [
                                {"total_lots": "5", "lot_type": "H", "lots_available": "2"},
                            ],
                        },
                    ],
                }
            ]
        }
        response = CarparkAvailabilityResponse.from_dict(data)
        available = response.available(lot_type=LotType.HEAVY_VEHICLE)
        assert len(available) == 1
        assert available[0].carpark_number == "HAS_H"
