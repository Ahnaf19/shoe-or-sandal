"""
Command-line interface for weather reminder bot.

Entry point that wires up all dependencies and executes use cases.
Implements Dependency Injection pattern.
"""

import logging
import sys
from typing import NoReturn

from src.presentation.config import AppConfig
from src.domain.exceptions import (
    DomainException,
    ConfigurationException,
)

# Import infrastructure implementations
from src.infrastructure.weather.open_meteo import OpenMeteoWeatherProvider
from src.infrastructure.messaging.telegram import TelegramNotificationService
from src.infrastructure.persistence.sqlite_repo import SQLiteWeatherRepository

# Import application services and use cases
from src.application.services import (
    RainBasedRecommendationService,
    MessageFormatter,
)
from src.application.use_cases import (
    SendWeatherReminderUseCase,
    GetWeatherStatisticsUseCase,
    VerifySystemHealthUseCase,
)

logger = logging.getLogger(__name__)


class WeatherReminderCLI:
    """
    Command-line interface for weather reminder application.

    Handles dependency injection and orchestrates the application flow.
    """

    def __init__(self, config: AppConfig) -> None:
        """
        Initialize CLI with configuration.

        Args:
            config: Application configuration
        """
        self.config = config
        logger.info("Initializing WeatherReminderCLI")

    def run(self) -> int:
        """
        Run the weather reminder workflow.

        Returns:
            Exit code (0 for success, 1 for failure)
        """
        try:
            logger.info("=" * 60)
            logger.info("Weather Reminder Bot Started")
            logger.info("=" * 60)
            logger.info(f"\n{self.config.summary()}\n")

            # Initialize dependencies (Dependency Injection)
            logger.info("Initializing services...")

            weather_provider = OpenMeteoWeatherProvider(
                timeout=self.config.weather.api_timeout,
                max_retries=self.config.weather.api_max_retries,
            )

            notification_service = TelegramNotificationService(
                bot_token=self.config.telegram.bot_token,
                chat_id=self.config.telegram.chat_id,
            )

            weather_repository = SQLiteWeatherRepository(
                db_path=self.config.database.path
            )

            recommendation_service = RainBasedRecommendationService(
                rain_threshold=self.config.weather.rain_threshold
            )

            message_formatter = MessageFormatter()

            # Verify system health
            logger.info("Verifying system health...")
            health_check_use_case = VerifySystemHealthUseCase(
                weather_provider=weather_provider,
                notification_service=notification_service,
                weather_repository=weather_repository,
                location=self.config.location.location,
            )

            health = health_check_use_case.execute()

            if not health["overall"]:
                logger.error("System health check failed!")
                logger.error(f"Health status: {health}")
                return 1

            logger.info("System health check passed ✓")

            # Execute main use case
            logger.info("\nExecuting weather reminder workflow...")

            use_case = SendWeatherReminderUseCase(
                weather_provider=weather_provider,
                notification_service=notification_service,
                weather_repository=weather_repository,
                recommendation_service=recommendation_service,
                message_formatter=message_formatter,
                rain_threshold=self.config.weather.rain_threshold,
            )

            result = use_case.execute(location=self.config.location.location)

            # Log results
            logger.info("\nWorkflow execution completed:")
            logger.info(f"  Success: {result.success}")
            logger.info(f"  Message Sent: {result.message_sent}")
            logger.info(f"  Data Saved: {result.data_saved}")
            if result.recommendation:
                logger.info(f"  Recommendation: {result.recommendation.value}")
            if result.error:
                logger.error(f"  Error: {result.error}")

            # Show statistics if data was saved
            if result.data_saved:
                logger.info("\nRetrieving dataset statistics...")
                stats_use_case = GetWeatherStatisticsUseCase(weather_repository)
                stats = stats_use_case.execute()

                logger.info("\nML Dataset Statistics:")
                logger.info(f"  Total days recorded: {stats.total_days}")
                logger.info(f"  Rainy days: {stats.rainy_days}")
                logger.info(f"  Rainy days percentage: {stats.rainy_days_percentage():.1f}%")
                logger.info(f"  Average rain probability: {stats.average_rain_probability}%")
                logger.info(f"  Average temperature: {stats.average_temperature}°C")
                logger.info(f"  Sandal recommendations: {stats.sandal_recommendations}")
                logger.info(f"  Shoe recommendations: {stats.shoe_recommendations}")

            logger.info("\n" + "=" * 60)
            logger.info("Weather Reminder Bot Completed")
            logger.info("=" * 60)

            return 0 if result.success else 1

        except ConfigurationException as e:
            logger.error(f"Configuration error: {e.message}")
            logger.error("Please check your .env file and ensure all required variables are set.")
            return 1

        except DomainException as e:
            logger.error(f"Domain error: {e.message}", exc_info=True)
            return 1

        except KeyboardInterrupt:
            logger.info("\nBot interrupted by user")
            return 0

        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}", exc_info=True)
            return 1


def setup_logging(config: AppConfig) -> None:
    """
    Configure application logging.

    Args:
        config: Application configuration with logging settings
    """
    log_level = getattr(logging, config.logging.level)

    # Create handlers
    handlers = [logging.StreamHandler(sys.stdout)]

    # Add file handler if log file specified
    if config.logging.log_file:
        handlers.append(logging.FileHandler(config.logging.log_file))

    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format=config.logging.format,
        handlers=handlers,
    )

    # Set levels for noisy libraries
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    logger.info(f"Logging configured: level={config.logging.level}")


def main() -> NoReturn:
    """
    Main entry point for CLI application.

    Loads configuration, sets up logging, and runs the application.
    """
    try:
        # Load configuration
        config = AppConfig.from_env()
        config.validate()

        # Setup logging
        setup_logging(config)

        # Run application
        cli = WeatherReminderCLI(config)
        exit_code = cli.run()

        sys.exit(exit_code)

    except ConfigurationException as e:
        # Can't use logger yet if configuration failed
        print(f"Configuration Error: {e.message}", file=sys.stderr)
        print("Please check your .env file.", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Fatal Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
