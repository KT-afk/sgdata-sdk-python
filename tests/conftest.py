"""Shared test fixtures and configuration for pytest."""

import pytest
from unittest.mock import Mock
import requests

from sgdata.client import SGDataClient


@pytest.fixture
def client():
    """Create a SGDataClient instance for testing.

    Returns:
        SGDataClient: A fresh client instance.

    Note:
        This fixture automatically closes the client after each test.
    """
    client = SGDataClient()
    yield client
    client.close()


@pytest.fixture
def mock_response():
    """Create a mock HTTP response.

    Returns:
        Mock: A mock response object with common attributes.
    """
    response = Mock()
    response.status_code = 200
    response.json.return_value = {"data": "test"}
    return response


@pytest.fixture
def mock_error_response():
    """Create a mock HTTP error response.

    Returns:
        Mock: A mock response object configured for error scenarios.
    """
    response = Mock()
    response.status_code = 500
    response.raise_for_status.side_effect = requests.HTTPError("500 Internal Server Error")
    return response


@pytest.fixture
def sample_psi_data():
    """Sample PSI data response.

    Returns:
        dict: Mock PSI data matching the API response format.
    """
    return {
        "region_metadata": [
            {"name": "west", "label_location": {"latitude": 1.35735, "longitude": 103.7}},
            {"name": "national", "label_location": {"latitude": 0, "longitude": 0}},
            {"name": "east", "label_location": {"latitude": 1.35735, "longitude": 103.94}},
            {"name": "central", "label_location": {"latitude": 1.35735, "longitude": 103.82}},
            {"name": "south", "label_location": {"latitude": 1.29587, "longitude": 103.82}},
            {"name": "north", "label_location": {"latitude": 1.41803, "longitude": 103.82}}
        ],
        "items": [
            {
                "timestamp": "2024-01-15T12:00:00+08:00",
                "update_timestamp": "2024-01-15T12:06:00+08:00",
                "readings": {
                    "o3_sub_index": {"west": 15, "national": 18, "east": 18, "central": 16, "south": 14, "north": 20},
                    "pm10_twenty_four_hourly": {"west": 25, "national": 28, "east": 27, "central": 24, "south": 22, "north": 30},
                    "pm10_sub_index": {"west": 25, "national": 28, "east": 27, "central": 24, "south": 22, "north": 30},
                    "co_sub_index": {"west": 3, "national": 4, "east": 4, "central": 3, "south": 3, "north": 4},
                    "pm25_twenty_four_hourly": {"west": 12, "national": 14, "east": 13, "central": 11, "south": 10, "north": 15},
                    "so2_sub_index": {"west": 2, "national": 3, "east": 2, "central": 2, "south": 2, "north": 3},
                    "co_eight_hour_max": {"west": 0.33, "national": 0.41, "east": 0.38, "central": 0.35, "south": 0.31, "north": 0.44},
                    "no2_one_hour_max": {"west": 12, "national": 15, "east": 14, "central": 13, "south": 11, "north": 16},
                    "so2_twenty_four_hourly": {"west": 3, "national": 4, "east": 3, "central": 3, "south": 3, "north": 4},
                    "pm25_sub_index": {"west": 50, "national": 58, "east": 54, "central": 46, "south": 42, "north": 62},
                    "psi_twenty_four_hourly": {"west": 50, "national": 58, "east": 54, "central": 46, "south": 42, "north": 62},
                    "o3_eight_hour_max": {"west": 18, "national": 22, "east": 21, "central": 19, "south": 17, "north": 24}
                }
            }
        ],
        "api_info": {"status": "healthy"}
    }


@pytest.fixture
def sample_weather_forecast_data():
    """Sample 2-hour weather forecast data.

    Returns:
        dict: Mock weather forecast data matching the API response format.
    """
    return {
        "area_metadata": [
            {"name": "Ang Mo Kio", "label_location": {"latitude": 1.375, "longitude": 103.839}},
            {"name": "Bedok", "label_location": {"latitude": 1.321, "longitude": 103.924}},
            {"name": "Bishan", "label_location": {"latitude": 1.350772, "longitude": 103.839}}
        ],
        "items": [
            {
                "update_timestamp": "2024-01-15T12:00:00+08:00",
                "timestamp": "2024-01-15T12:00:00+08:00",
                "valid_period": {
                    "start": "2024-01-15T12:00:00+08:00",
                    "end": "2024-01-15T14:00:00+08:00"
                },
                "forecasts": [
                    {"area": "Ang Mo Kio", "forecast": "Partly Cloudy"},
                    {"area": "Bedok", "forecast": "Partly Cloudy"},
                    {"area": "Bishan", "forecast": "Light Rain"}
                ]
            }
        ],
        "api_info": {"status": "healthy"}
    }


@pytest.fixture
def sample_carpark_data():
    """Sample carpark availability data.

    Returns:
        dict: Mock carpark data matching the API response format.
    """
    return {
        "items": [
            {
                "timestamp": "2024-01-15T12:00:00+08:00",
                "carpark_data": [
                    {
                        "carpark_info": [
                            {
                                "total_lots": "100",
                                "lot_type": "C",
                                "lots_available": "50"
                            }
                        ],
                        "carpark_number": "HG1",
                        "update_datetime": "2024-01-15T12:00:00"
                    },
                    {
                        "carpark_info": [
                            {
                                "total_lots": "200",
                                "lot_type": "C",
                                "lots_available": "120"
                            }
                        ],
                        "carpark_number": "HG2",
                        "update_datetime": "2024-01-15T12:00:00"
                    }
                ]
            }
        ],
        "api_info": {"status": "healthy"}
    }
