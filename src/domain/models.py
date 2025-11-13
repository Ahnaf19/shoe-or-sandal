"""
Domain models - Core business entities.

These are immutable value objects and entities representing our domain.
Following domain-driven design principles.
"""

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
from typing import Optional


class FootwearRecommendation(Enum):
    """Enumeration of possible footwear recommendations."""

    SANDAL = "sandal"
    SHOE = "shoe"


class WeatherCondition(Enum):
    """Enumeration of weather conditions."""

    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    CLOUDY = "cloudy"
    RAINY = "rainy"
    STORMY = "stormy"
    FOGGY = "foggy"
    SNOWY = "snowy"


@dataclass(frozen=True)
class Location:
    """Value object representing a geographic location."""

    latitude: float
    longitude: float
    name: str = "Unknown"
    timezone: str = "UTC"

    def __post_init__(self) -> None:
        """Validate location data."""
        if not -90 <= self.latitude <= 90:
            raise ValueError(f"Invalid latitude: {self.latitude}")
        if not -180 <= self.longitude <= 180:
            raise ValueError(f"Invalid longitude: {self.longitude}")


@dataclass(frozen=True)
class WeatherForecast:
    """
    Value object representing weather forecast data.

    This is the core domain model containing all weather information.
    """

    rain_probability: int
    temperature: float
    humidity: float
    condition: str
    timestamp: datetime
    location: Location

    def __post_init__(self) -> None:
        """Validate weather data."""
        if not 0 <= self.rain_probability <= 100:
            raise ValueError(f"Invalid rain probability: {self.rain_probability}")
        if not 0 <= self.humidity <= 100:
            raise ValueError(f"Invalid humidity: {self.humidity}")
        if self.temperature < -100 or self.temperature > 60:
            raise ValueError(f"Invalid temperature: {self.temperature}")

    def is_rainy(self) -> bool:
        """Determine if weather conditions indicate rain."""
        rain_keywords = ["rain", "drizzle", "shower", "storm", "thunderstorm"]
        return any(keyword in self.condition.lower() for keyword in rain_keywords)


@dataclass(frozen=True)
class WeatherRecommendation:
    """
    Value object representing a footwear recommendation.

    This encapsulates the business decision based on weather.
    """

    forecast: WeatherForecast
    recommendation: FootwearRecommendation
    reason: str
    confidence: float = 1.0

    def __post_init__(self) -> None:
        """Validate recommendation data."""
        if not 0 <= self.confidence <= 1:
            raise ValueError(f"Invalid confidence: {self.confidence}")


@dataclass
class WeatherRecord:
    """
    Entity representing a stored weather record.

    Mutable entity for database persistence.
    """

    date: date
    rain_probability: int
    actual_rained: bool
    temperature: float
    humidity: float
    weather_condition: str
    recommendation: FootwearRecommendation
    location: Location
    raw_data: Optional[str] = None
    message_sent_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "date": self.date.isoformat(),
            "rain_probability": self.rain_probability,
            "actual_rained": self.actual_rained,
            "temperature": self.temperature,
            "humidity": self.humidity,
            "weather_condition": self.weather_condition,
            "recommendation": self.recommendation.value,
            "location_name": self.location.name,
            "raw_data": self.raw_data,
            "message_sent_at": self.message_sent_at.isoformat() if self.message_sent_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


@dataclass(frozen=True)
class WeatherStatistics:
    """Value object for weather history statistics."""

    total_days: int
    rainy_days: int
    average_rain_probability: float
    average_temperature: float
    sandal_recommendations: int
    shoe_recommendations: int

    def rainy_days_percentage(self) -> float:
        """Calculate percentage of rainy days."""
        if self.total_days == 0:
            return 0.0
        return (self.rainy_days / self.total_days) * 100
