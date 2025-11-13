"""
Open-Meteo weather provider implementation.

Concrete implementation of WeatherProvider interface using Open-Meteo API.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List
import requests

from src.domain.models import Location, WeatherForecast
from src.domain.repositories import WeatherProvider
from src.domain.exceptions import WeatherDataException, ExternalServiceException

logger = logging.getLogger(__name__)


class OpenMeteoWeatherProvider(WeatherProvider):
    """
    Weather provider using Open-Meteo API.

    Open-Meteo is free, requires no API key, and provides reliable forecasts.
    """

    API_BASE_URL = "https://api.open-meteo.com/v1/forecast"
    TIMEOUT_SECONDS = 10
    MAX_RETRIES = 3

    # WMO Weather interpretation codes
    WEATHER_CODE_MAP = {
        0: "Clear sky",
        1: "Mainly clear",
        2: "Partly cloudy",
        3: "Overcast",
        45: "Foggy",
        48: "Depositing rime fog",
        51: "Light drizzle",
        53: "Moderate drizzle",
        55: "Dense drizzle",
        61: "Slight rain",
        63: "Moderate rain",
        65: "Heavy rain",
        71: "Slight snow",
        73: "Moderate snow",
        75: "Heavy snow",
        77: "Snow grains",
        80: "Slight rain showers",
        81: "Moderate rain showers",
        82: "Violent rain showers",
        85: "Slight snow showers",
        86: "Heavy snow showers",
        95: "Thunderstorm",
        96: "Thunderstorm with slight hail",
        99: "Thunderstorm with heavy hail",
    }

    def __init__(self, timeout: int = TIMEOUT_SECONDS, max_retries: int = MAX_RETRIES) -> None:
        """
        Initialize Open-Meteo provider.

        Args:
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts
        """
        self._timeout = timeout
        self._max_retries = max_retries
        logger.info(f"Initialized OpenMeteoWeatherProvider (timeout={timeout}s, retries={max_retries})")

    def get_forecast(self, location: Location) -> WeatherForecast:
        """
        Fetch current weather forecast for location.

        Args:
            location: Location to get forecast for

        Returns:
            WeatherForecast with current conditions

        Raises:
            WeatherDataException: If unable to fetch or parse data
            ExternalServiceException: If API request fails
        """
        logger.info(f"Fetching forecast for {location.name} ({location.latitude}, {location.longitude})")

        try:
            data = self._fetch_weather_data(location)
            return self._parse_current_forecast(data, location)

        except requests.RequestException as e:
            error_msg = f"Failed to fetch weather data: {str(e)}"
            logger.error(error_msg)
            raise ExternalServiceException("Open-Meteo API", error_msg) from e

        except (KeyError, IndexError, ValueError) as e:
            error_msg = f"Failed to parse weather data: {str(e)}"
            logger.error(error_msg)
            raise WeatherDataException(error_msg) from e

    def get_morning_forecast(
        self, location: Location, start_hour: int = 8, end_hour: int = 12
    ) -> WeatherForecast:
        """
        Fetch weather forecast for morning hours.

        Args:
            location: Location to get forecast for
            start_hour: Start of morning window (default 8 AM)
            end_hour: End of morning window (default 12 PM)

        Returns:
            WeatherForecast aggregated for morning period

        Raises:
            WeatherDataException: If unable to fetch or parse data
        """
        logger.info(
            f"Fetching morning forecast ({start_hour}-{end_hour}) for {location.name}"
        )

        try:
            data = self._fetch_weather_data(location)
            return self._parse_morning_forecast(data, location, start_hour, end_hour)

        except requests.RequestException as e:
            error_msg = f"Failed to fetch weather data: {str(e)}"
            logger.error(error_msg)
            raise ExternalServiceException("Open-Meteo API", error_msg) from e

        except (KeyError, IndexError, ValueError) as e:
            error_msg = f"Failed to parse weather data: {str(e)}"
            logger.error(error_msg)
            raise WeatherDataException(error_msg) from e

    def _fetch_weather_data(self, location: Location) -> Dict[str, Any]:
        """
        Fetch raw weather data from Open-Meteo API with retry logic.

        Args:
            location: Location to fetch data for

        Returns:
            Raw JSON response as dictionary

        Raises:
            requests.RequestException: If all retry attempts fail
        """
        params = {
            "latitude": location.latitude,
            "longitude": location.longitude,
            "hourly": "temperature_2m,relative_humidity_2m,precipitation_probability,weather_code",
            "timezone": location.timezone,
            "forecast_days": 1,
        }

        last_exception = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.debug(f"API request attempt {attempt}/{self._max_retries}")
                response = requests.get(
                    self.API_BASE_URL,
                    params=params,
                    timeout=self._timeout,
                )
                response.raise_for_status()

                data = response.json()
                logger.debug("Successfully fetched weather data")
                return data

            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} failed: {e}")

                if attempt < self._max_retries:
                    wait_time = 2 ** (attempt - 1)  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    import time
                    time.sleep(wait_time)

        # All retries failed
        error_msg = f"All {self._max_retries} attempts failed"
        logger.error(error_msg)
        raise last_exception or requests.RequestException(error_msg)

    def _parse_current_forecast(
        self, data: Dict[str, Any], location: Location
    ) -> WeatherForecast:
        """
        Parse current weather from API response.

        Args:
            data: Raw API response
            location: Location data

        Returns:
            WeatherForecast for current time
        """
        hourly = data["hourly"]
        times = hourly["time"]
        temperatures = hourly["temperature_2m"]
        humidities = hourly["relative_humidity_2m"]
        rain_probs = hourly["precipitation_probability"]
        weather_codes = hourly["weather_code"]

        # Get first available data point (current hour)
        index = 0

        return WeatherForecast(
            rain_probability=int(rain_probs[index] or 0),
            temperature=float(temperatures[index]),
            humidity=float(humidities[index]),
            condition=self._get_weather_description(weather_codes[index]),
            timestamp=datetime.fromisoformat(times[index]),
            location=location,
        )

    def _parse_morning_forecast(
        self,
        data: Dict[str, Any],
        location: Location,
        start_hour: int,
        end_hour: int,
    ) -> WeatherForecast:
        """
        Parse morning weather forecast from API response.

        Aggregates hourly data for the morning window.

        Args:
            data: Raw API response
            location: Location data
            start_hour: Start of morning window
            end_hour: End of morning window

        Returns:
            WeatherForecast aggregated for morning

        Raises:
            WeatherDataException: If no morning data found
        """
        hourly = data["hourly"]
        times = hourly["time"]
        temperatures = hourly["temperature_2m"]
        humidities = hourly["relative_humidity_2m"]
        rain_probs = hourly["precipitation_probability"]
        weather_codes = hourly["weather_code"]

        # Extract morning hours
        morning_indices = self._find_morning_indices(times, start_hour, end_hour)

        if not morning_indices:
            raise WeatherDataException(
                f"No morning hours ({start_hour}-{end_hour}) found in forecast"
            )

        # Aggregate morning data
        morning_rain_probs = [rain_probs[i] or 0 for i in morning_indices]
        morning_temps = [temperatures[i] for i in morning_indices]
        morning_humidities = [humidities[i] for i in morning_indices]
        morning_codes = [weather_codes[i] for i in morning_indices]

        # Calculate statistics
        max_rain_prob = int(max(morning_rain_probs))
        avg_temp = sum(morning_temps) / len(morning_temps)
        avg_humidity = sum(morning_humidities) / len(morning_humidities)
        primary_code = morning_codes[0]  # Use first hour's code

        logger.debug(
            f"Morning forecast: rain={max_rain_prob}%, "
            f"temp={avg_temp:.1f}°C, humidity={avg_humidity:.1f}%"
        )

        return WeatherForecast(
            rain_probability=max_rain_prob,
            temperature=round(avg_temp, 1),
            humidity=round(avg_humidity, 1),
            condition=self._get_weather_description(primary_code),
            timestamp=datetime.fromisoformat(times[morning_indices[0]]),
            location=location,
        )

    def _find_morning_indices(
        self, times: List[str], start_hour: int, end_hour: int
    ) -> List[int]:
        """
        Find indices of hourly data that fall within morning window.

        Args:
            times: List of ISO timestamp strings
            start_hour: Start hour (inclusive)
            end_hour: End hour (exclusive)

        Returns:
            List of indices for morning hours
        """
        morning_indices = []

        for i, time_str in enumerate(times):
            hour = int(time_str.split("T")[1].split(":")[0])
            if start_hour <= hour < end_hour:
                morning_indices.append(i)

        logger.debug(f"Found {len(morning_indices)} morning hours")
        return morning_indices

    def _get_weather_description(self, wmo_code: int) -> str:
        """
        Convert WMO weather code to human-readable description.

        Args:
            wmo_code: WMO weather interpretation code

        Returns:
            Weather description string
        """
        return self.WEATHER_CODE_MAP.get(wmo_code, "Unknown")
