"""
Domain repositories - Interface definitions (Ports).

These are abstract interfaces that define contracts for data access.
Infrastructure layer provides concrete implementations.

Following the Dependency Inversion Principle (SOLID).
"""

from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from src.domain.models import (
    Location,
    WeatherForecast,
    WeatherRecord,
    WeatherStatistics,
)


class WeatherProvider(ABC):
    """
    Abstract interface for weather data providers.

    This allows swapping weather APIs without changing business logic.
    """

    @abstractmethod
    def get_forecast(self, location: Location) -> WeatherForecast:
        """
        Fetch weather forecast for a location.

        Args:
            location: Geographic location to get forecast for

        Returns:
            WeatherForecast object

        Raises:
            WeatherDataException: If unable to fetch weather data
            ExternalServiceException: If external API fails
        """
        pass

    @abstractmethod
    def get_morning_forecast(
        self, location: Location, start_hour: int = 8, end_hour: int = 12
    ) -> WeatherForecast:
        """
        Fetch weather forecast for morning hours.

        Args:
            location: Geographic location
            start_hour: Start hour for morning window (default 8 AM)
            end_hour: End hour for morning window (default 12 PM)

        Returns:
            WeatherForecast for the morning period

        Raises:
            WeatherDataException: If unable to fetch or process data
        """
        pass


class NotificationService(ABC):
    """
    Abstract interface for notification services.

    Allows multiple notification channels (Telegram, SMS, email, etc.)
    """

    @abstractmethod
    def send_message(self, message: str) -> bool:
        """
        Send a notification message.

        Args:
            message: Message content to send

        Returns:
            True if sent successfully, False otherwise

        Raises:
            NotificationException: If unable to send notification
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if notification service is available and configured.

        Returns:
            True if service is ready, False otherwise
        """
        pass


class WeatherRepository(ABC):
    """
    Abstract interface for weather data persistence.

    Defines contract for storing and retrieving weather records.
    """

    @abstractmethod
    def save(self, record: WeatherRecord) -> bool:
        """
        Persist a weather record.

        Args:
            record: WeatherRecord to save

        Returns:
            True if saved successfully

        Raises:
            PersistenceException: If unable to save data
        """
        pass

    @abstractmethod
    def find_by_date(self, record_date: date) -> Optional[WeatherRecord]:
        """
        Retrieve weather record for a specific date.

        Args:
            record_date: Date to search for

        Returns:
            WeatherRecord if found, None otherwise
        """
        pass

    @abstractmethod
    def find_all(self) -> List[WeatherRecord]:
        """
        Retrieve all weather records.

        Returns:
            List of all WeatherRecord objects
        """
        pass

    @abstractmethod
    def get_statistics(self) -> WeatherStatistics:
        """
        Calculate statistics from stored records.

        Returns:
            WeatherStatistics object with aggregated data
        """
        pass

    @abstractmethod
    def count_rainy_days(self) -> int:
        """
        Count number of days that actually rained.

        Returns:
            Number of rainy days
        """
        pass
