"""
Application use cases - High-level business workflows.

Use cases orchestrate domain objects and services to fulfill business requirements.
Each use case represents a single user action or system operation.
"""

import logging
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from src.domain.models import (
    Location,
    WeatherRecord,
    FootwearRecommendation,
)
from src.domain.repositories import (
    WeatherProvider,
    NotificationService,
    WeatherRepository,
)
from src.domain.exceptions import (
    WeatherDataException,
    NotificationException,
    PersistenceException,
)
from src.application.services import (
    RainBasedRecommendationService,
    MessageFormatter,
)

logger = logging.getLogger(__name__)


@dataclass
class SendWeatherReminderResult:
    """Result of sending weather reminder use case."""

    success: bool
    message_sent: bool
    data_saved: bool
    recommendation: Optional[FootwearRecommendation] = None
    error: Optional[str] = None


class SendWeatherReminderUseCase:
    """
    Use case: Send daily weather reminder with footwear recommendation.

    This is the main workflow of the application.
    Orchestrates: weather fetching → recommendation → notification → persistence

    Follows Single Responsibility and Dependency Inversion principles.
    """

    def __init__(
        self,
        weather_provider: WeatherProvider,
        notification_service: NotificationService,
        weather_repository: WeatherRepository,
        recommendation_service: RainBasedRecommendationService,
        message_formatter: MessageFormatter,
        rain_threshold: int = 30,
    ) -> None:
        """
        Initialize use case with dependencies (Dependency Injection).

        Args:
            weather_provider: Service to fetch weather data
            notification_service: Service to send notifications
            weather_repository: Repository to persist data
            recommendation_service: Service to generate recommendations
            message_formatter: Service to format messages
            rain_threshold: Threshold for storing data
        """
        self._weather_provider = weather_provider
        self._notification_service = notification_service
        self._weather_repository = weather_repository
        self._recommendation_service = recommendation_service
        self._message_formatter = message_formatter
        self._rain_threshold = rain_threshold

        logger.info("Initialized SendWeatherReminderUseCase")

    def execute(self, location: Location) -> SendWeatherReminderResult:
        """
        Execute the weather reminder workflow.

        Steps:
        1. Fetch morning weather forecast
        2. Generate footwear recommendation
        3. Format and send notification
        4. Persist data if conditions met

        Args:
            location: Location to get weather for

        Returns:
            SendWeatherReminderResult with execution details
        """
        logger.info(f"Executing SendWeatherReminder for {location.name}")

        message_sent = False
        data_saved = False
        recommendation = None
        error_message = None

        try:
            # Step 1: Fetch weather forecast
            logger.info("Fetching morning weather forecast...")
            forecast = self._weather_provider.get_morning_forecast(location)
            logger.info(
                f"Weather: {forecast.condition}, rain={forecast.rain_probability}%, "
                f"temp={forecast.temperature}°C"
            )

            # Step 2: Generate recommendation
            logger.info("Generating footwear recommendation...")
            weather_recommendation = self._recommendation_service.recommend(forecast)
            recommendation = weather_recommendation.recommendation
            logger.info(f"Recommendation: {recommendation.value} (confidence={weather_recommendation.confidence})")

            # Step 3: Format and send notification
            logger.info("Sending notification...")
            message = self._message_formatter.format_weather_recommendation(
                weather_recommendation
            )

            message_sent = self._notification_service.send_message(message)
            if message_sent:
                logger.info("Notification sent successfully")
            else:
                logger.warning("Failed to send notification")

            # Step 4: Persist data if conditions met
            should_save = self._should_save_data(
                forecast.rain_probability,
                forecast.is_rainy(),
            )

            if should_save:
                logger.info("Saving weather data to repository...")
                data_saved = self._save_weather_record(
                    forecast, weather_recommendation
                )
                if data_saved:
                    logger.info("Weather data saved successfully")
                    stats = self._weather_repository.get_statistics()
                    logger.info(f"Dataset stats: {stats.total_days} days, {stats.rainy_days} rainy")
                else:
                    logger.warning("Failed to save weather data")
            else:
                logger.info(
                    f"Skipping data storage: rain_probability={forecast.rain_probability}% "
                    f"< threshold={self._rain_threshold}%"
                )

            success = message_sent  # Consider successful if message was sent
            return SendWeatherReminderResult(
                success=success,
                message_sent=message_sent,
                data_saved=data_saved,
                recommendation=recommendation,
            )

        except WeatherDataException as e:
            error_message = f"Weather data error: {e.message}"
            logger.error(error_message, exc_info=True)
            self._send_error_notification(e)

        except NotificationException as e:
            error_message = f"Notification error: {e.message}"
            logger.error(error_message, exc_info=True)

        except PersistenceException as e:
            error_message = f"Persistence error: {e.message}"
            logger.error(error_message, exc_info=True)
            # Don't fail the entire operation if just persistence fails

        except Exception as e:
            error_message = f"Unexpected error: {str(e)}"
            logger.error(error_message, exc_info=True)
            self._send_error_notification(e)

        return SendWeatherReminderResult(
            success=False,
            message_sent=message_sent,
            data_saved=data_saved,
            recommendation=recommendation,
            error=error_message,
        )

    def _should_save_data(self, rain_probability: int, is_rainy: bool) -> bool:
        """
        Determine if weather data should be saved.

        Data is saved when:
        - Rain probability >= threshold, OR
        - It's actually raining

        This builds a useful ML dataset with both positive and negative examples.

        Args:
            rain_probability: Rain probability percentage
            is_rainy: Whether it's actually raining

        Returns:
            True if data should be saved
        """
        return rain_probability >= self._rain_threshold or is_rainy

    def _save_weather_record(
        self,
        forecast,
        recommendation,
    ) -> bool:
        """
        Save weather record to repository.

        Args:
            forecast: WeatherForecast to save
            recommendation: WeatherRecommendation generated

        Returns:
            True if saved successfully
        """
        try:
            record = WeatherRecord(
                date=forecast.timestamp.date(),
                rain_probability=forecast.rain_probability,
                actual_rained=forecast.is_rainy(),
                temperature=forecast.temperature,
                humidity=forecast.humidity,
                weather_condition=forecast.condition,
                recommendation=recommendation.recommendation,
                location=forecast.location,
                raw_data=None,  # Could serialize full forecast here
                message_sent_at=datetime.now(),
                created_at=datetime.now(),
            )

            return self._weather_repository.save(record)

        except Exception as e:
            logger.error(f"Failed to save weather record: {e}", exc_info=True)
            raise PersistenceException(f"Failed to save weather record: {e}") from e

    def _send_error_notification(self, error: Exception) -> None:
        """
        Attempt to send error notification to user.

        Args:
            error: The exception that occurred
        """
        try:
            error_message = self._message_formatter.format_error_message(error)
            self._notification_service.send_message(error_message)
        except Exception as e:
            logger.error(f"Failed to send error notification: {e}")


class GetWeatherStatisticsUseCase:
    """
    Use case: Retrieve weather history statistics.

    Useful for viewing ML dataset progress.
    """

    def __init__(self, weather_repository: WeatherRepository) -> None:
        """
        Initialize use case.

        Args:
            weather_repository: Repository to query statistics from
        """
        self._weather_repository = weather_repository
        logger.info("Initialized GetWeatherStatisticsUseCase")

    def execute(self):
        """
        Retrieve and return weather statistics.

        Returns:
            WeatherStatistics object
        """
        logger.info("Retrieving weather statistics...")
        stats = self._weather_repository.get_statistics()
        logger.info(f"Statistics retrieved: {stats.total_days} total days")
        return stats


class VerifySystemHealthUseCase:
    """
    Use case: Verify all system components are working.

    Useful for deployment health checks.
    """

    def __init__(
        self,
        weather_provider: WeatherProvider,
        notification_service: NotificationService,
        weather_repository: WeatherRepository,
        location: Location,
    ) -> None:
        """
        Initialize use case.

        Args:
            weather_provider: Weather provider to check
            notification_service: Notification service to check
            weather_repository: Repository to check
            location: Test location for weather check
        """
        self._weather_provider = weather_provider
        self._notification_service = notification_service
        self._weather_repository = weather_repository
        self._location = location

        logger.info("Initialized VerifySystemHealthUseCase")

    def execute(self) -> dict:
        """
        Check health of all system components.

        Returns:
            Dictionary with health status of each component
        """
        logger.info("Verifying system health...")

        health = {
            "weather_provider": False,
            "notification_service": False,
            "weather_repository": False,
            "overall": False,
        }

        # Check weather provider
        try:
            forecast = self._weather_provider.get_forecast(self._location)
            health["weather_provider"] = forecast is not None
            logger.info("Weather provider: OK")
        except Exception as e:
            logger.error(f"Weather provider check failed: {e}")

        # Check notification service
        try:
            health["notification_service"] = self._notification_service.test_connection()
            logger.info(f"Notification service: {'OK' if health['notification_service'] else 'FAILED'}")
        except Exception as e:
            logger.error(f"Notification service check failed: {e}")

        # Check weather repository
        try:
            stats = self._weather_repository.get_statistics()
            health["weather_repository"] = stats is not None
            logger.info("Weather repository: OK")
        except Exception as e:
            logger.error(f"Weather repository check failed: {e}")

        # Overall health
        health["overall"] = all([
            health["weather_provider"],
            health["notification_service"],
            health["weather_repository"],
        ])

        logger.info(f"System health: {'HEALTHY' if health['overall'] else 'UNHEALTHY'}")
        return health
