"""
Application configuration.

Centralized configuration management with validation.
Loads settings from environment variables.
"""

import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

from src.domain.models import Location
from src.domain.exceptions import ConfigurationException

# Load environment variables from .env file
load_dotenv()


@dataclass(frozen=True)
class TelegramConfig:
    """Telegram bot configuration."""

    bot_token: str
    chat_id: str

    @classmethod
    def from_env(cls) -> "TelegramConfig":
        """Load from environment variables."""
        bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "")

        if not bot_token:
            raise ConfigurationException("TELEGRAM_BOT_TOKEN is required")
        if not chat_id:
            raise ConfigurationException("TELEGRAM_CHAT_ID is required")

        return cls(bot_token=bot_token, chat_id=chat_id)


@dataclass(frozen=True)
class DatabaseConfig:
    """Database configuration."""

    path: str

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load from environment variables."""
        path = os.getenv("DATABASE_PATH", "weather_history.db")
        return cls(path=path)


@dataclass(frozen=True)
class WeatherConfig:
    """Weather service configuration."""

    rain_threshold: int
    api_timeout: int
    api_max_retries: int

    @classmethod
    def from_env(cls) -> "WeatherConfig":
        """Load from environment variables with defaults."""
        rain_threshold = int(os.getenv("RAIN_THRESHOLD", "30"))
        api_timeout = int(os.getenv("WEATHER_API_TIMEOUT", "10"))
        api_max_retries = int(os.getenv("WEATHER_API_MAX_RETRIES", "3"))

        # Validate
        if not 0 <= rain_threshold <= 100:
            raise ConfigurationException(
                f"RAIN_THRESHOLD must be 0-100, got {rain_threshold}"
            )

        if api_timeout <= 0:
            raise ConfigurationException(
                f"WEATHER_API_TIMEOUT must be positive, got {api_timeout}"
            )

        if api_max_retries <= 0:
            raise ConfigurationException(
                f"WEATHER_API_MAX_RETRIES must be positive, got {api_max_retries}"
            )

        return cls(
            rain_threshold=rain_threshold,
            api_timeout=api_timeout,
            api_max_retries=api_max_retries,
        )


@dataclass(frozen=True)
class LocationConfig:
    """Location configuration."""

    location: Location

    @classmethod
    def from_env(cls) -> "LocationConfig":
        """Load from environment variables."""
        name = os.getenv("LOCATION_NAME", "Dhaka")
        latitude = float(os.getenv("LOCATION_LATITUDE", "23.8103"))
        longitude = float(os.getenv("LOCATION_LONGITUDE", "90.4125"))
        timezone = os.getenv("TIMEZONE", "Asia/Dhaka")

        try:
            location = Location(
                latitude=latitude,
                longitude=longitude,
                name=name,
                timezone=timezone,
            )
            return cls(location=location)
        except ValueError as e:
            raise ConfigurationException(f"Invalid location configuration: {e}") from e


@dataclass(frozen=True)
class LoggingConfig:
    """Logging configuration."""

    level: str
    format: str
    log_file: Optional[str]

    @classmethod
    def from_env(cls) -> "LoggingConfig":
        """Load from environment variables."""
        level = os.getenv("LOG_LEVEL", "INFO").upper()
        format_str = os.getenv(
            "LOG_FORMAT",
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        log_file = os.getenv("LOG_FILE")

        # Validate log level
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if level not in valid_levels:
            raise ConfigurationException(
                f"LOG_LEVEL must be one of {valid_levels}, got {level}"
            )

        return cls(level=level, format=format_str, log_file=log_file)


@dataclass(frozen=True)
class AppConfig:
    """
    Complete application configuration.

    Aggregates all configuration components.
    """

    telegram: TelegramConfig
    database: DatabaseConfig
    weather: WeatherConfig
    location: LocationConfig
    logging: LoggingConfig

    @classmethod
    def from_env(cls) -> "AppConfig":
        """
        Load complete configuration from environment.

        Returns:
            AppConfig instance with all settings

        Raises:
            ConfigurationException: If configuration is invalid or incomplete
        """
        try:
            return cls(
                telegram=TelegramConfig.from_env(),
                database=DatabaseConfig.from_env(),
                weather=WeatherConfig.from_env(),
                location=LocationConfig.from_env(),
                logging=LoggingConfig.from_env(),
            )
        except Exception as e:
            if isinstance(e, ConfigurationException):
                raise
            raise ConfigurationException(f"Failed to load configuration: {e}") from e

    def validate(self) -> None:
        """
        Validate configuration completeness.

        Raises:
            ConfigurationException: If validation fails
        """
        # All validation happens in from_env() methods
        # This is here for extensibility
        pass

    def summary(self) -> str:
        """
        Generate human-readable configuration summary.

        Returns:
            Multi-line string with configuration details
        """
        return f"""
Application Configuration:
-------------------------
Location: {self.location.location.name} ({self.location.location.latitude}, {self.location.location.longitude})
Timezone: {self.location.location.timezone}
Rain Threshold: {self.weather.rain_threshold}%
Database: {self.database.path}
Log Level: {self.logging.level}
Telegram Chat ID: {self.telegram.chat_id}
""".strip()
