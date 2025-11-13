"""Unit tests for domain models."""

import pytest
from datetime import datetime

from src.domain.models import (
    Location,
    WeatherForecast,
    WeatherRecommendation,
    FootwearRecommendation,
)


class TestLocation:
    """Tests for Location value object."""

    def test_valid_location(self):
        """Test creating a valid location."""
        location = Location(
            latitude=23.8103,
            longitude=90.4125,
            name="Dhaka",
            timezone="Asia/Dhaka"
        )
        assert location.latitude == 23.8103
        assert location.longitude == 90.4125
        assert location.name == "Dhaka"
        assert location.timezone == "Asia/Dhaka"

    def test_invalid_latitude_too_high(self):
        """Test that latitude > 90 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            Location(latitude=91, longitude=0)

    def test_invalid_latitude_too_low(self):
        """Test that latitude < -90 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid latitude"):
            Location(latitude=-91, longitude=0)

    def test_invalid_longitude_too_high(self):
        """Test that longitude > 180 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid longitude"):
            Location(latitude=0, longitude=181)

    def test_invalid_longitude_too_low(self):
        """Test that longitude < -180 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid longitude"):
            Location(latitude=0, longitude=-181)

    def test_location_is_immutable(self):
        """Test that Location is frozen (immutable)."""
        location = Location(latitude=0, longitude=0)
        with pytest.raises(Exception):  # FrozenInstanceError
            location.latitude = 10


class TestWeatherForecast:
    """Tests for WeatherForecast value object."""

    def setup_method(self):
        """Set up test fixtures."""
        self.location = Location(latitude=23.8103, longitude=90.4125, name="Dhaka")

    def test_valid_weather_forecast(self):
        """Test creating a valid weather forecast."""
        forecast = WeatherForecast(
            rain_probability=30,
            temperature=25.5,
            humidity=70,
            condition="Partly cloudy",
            timestamp=datetime.now(),
            location=self.location
        )
        assert forecast.rain_probability == 30
        assert forecast.temperature == 25.5
        assert forecast.humidity == 70
        assert forecast.condition == "Partly cloudy"

    def test_invalid_rain_probability_too_high(self):
        """Test that rain_probability > 100 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid rain probability"):
            WeatherForecast(
                rain_probability=101,
                temperature=25,
                humidity=70,
                condition="Clear",
                timestamp=datetime.now(),
                location=self.location
            )

    def test_invalid_rain_probability_negative(self):
        """Test that negative rain_probability raises ValueError."""
        with pytest.raises(ValueError, match="Invalid rain probability"):
            WeatherForecast(
                rain_probability=-1,
                temperature=25,
                humidity=70,
                condition="Clear",
                timestamp=datetime.now(),
                location=self.location
            )

    def test_invalid_humidity_too_high(self):
        """Test that humidity > 100 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid humidity"):
            WeatherForecast(
                rain_probability=0,
                temperature=25,
                humidity=101,
                condition="Clear",
                timestamp=datetime.now(),
                location=self.location
            )

    def test_invalid_temperature_too_high(self):
        """Test that temperature > 60 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid temperature"):
            WeatherForecast(
                rain_probability=0,
                temperature=61,
                humidity=50,
                condition="Clear",
                timestamp=datetime.now(),
                location=self.location
            )

    def test_invalid_temperature_too_low(self):
        """Test that temperature < -100 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid temperature"):
            WeatherForecast(
                rain_probability=0,
                temperature=-101,
                humidity=50,
                condition="Clear",
                timestamp=datetime.now(),
                location=self.location
            )

    def test_is_rainy_with_rain_keyword(self):
        """Test is_rainy() returns True when condition contains 'rain'."""
        forecast = WeatherForecast(
            rain_probability=50,
            temperature=25,
            humidity=80,
            condition="Light rain",
            timestamp=datetime.now(),
            location=self.location
        )
        assert forecast.is_rainy() is True

    def test_is_rainy_with_drizzle_keyword(self):
        """Test is_rainy() returns True when condition contains 'drizzle'."""
        forecast = WeatherForecast(
            rain_probability=40,
            temperature=25,
            humidity=75,
            condition="Light drizzle",
            timestamp=datetime.now(),
            location=self.location
        )
        assert forecast.is_rainy() is True

    def test_is_rainy_with_storm_keyword(self):
        """Test is_rainy() returns True when condition contains 'storm'."""
        forecast = WeatherForecast(
            rain_probability=80,
            temperature=25,
            humidity=90,
            condition="Thunderstorm",
            timestamp=datetime.now(),
            location=self.location
        )
        assert forecast.is_rainy() is True

    def test_is_not_rainy_with_clear_condition(self):
        """Test is_rainy() returns False for clear conditions."""
        forecast = WeatherForecast(
            rain_probability=0,
            temperature=25,
            humidity=50,
            condition="Clear sky",
            timestamp=datetime.now(),
            location=self.location
        )
        assert forecast.is_rainy() is False


class TestWeatherRecommendation:
    """Tests for WeatherRecommendation value object."""

    def setup_method(self):
        """Set up test fixtures."""
        self.location = Location(latitude=23.8103, longitude=90.4125, name="Dhaka")
        self.forecast = WeatherForecast(
            rain_probability=50,
            temperature=25,
            humidity=70,
            condition="Cloudy",
            timestamp=datetime.now(),
            location=self.location
        )

    def test_valid_recommendation(self):
        """Test creating a valid weather recommendation."""
        recommendation = WeatherRecommendation(
            forecast=self.forecast,
            recommendation=FootwearRecommendation.SANDAL,
            reason="Rain probability is high",
            confidence=0.85
        )
        assert recommendation.forecast == self.forecast
        assert recommendation.recommendation == FootwearRecommendation.SANDAL
        assert recommendation.reason == "Rain probability is high"
        assert recommendation.confidence == 0.85

    def test_invalid_confidence_too_high(self):
        """Test that confidence > 1 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid confidence"):
            WeatherRecommendation(
                forecast=self.forecast,
                recommendation=FootwearRecommendation.SANDAL,
                reason="Test",
                confidence=1.1
            )

    def test_invalid_confidence_negative(self):
        """Test that negative confidence raises ValueError."""
        with pytest.raises(ValueError, match="Invalid confidence"):
            WeatherRecommendation(
                forecast=self.forecast,
                recommendation=FootwearRecommendation.SHOE,
                reason="Test",
                confidence=-0.1
            )

    def test_default_confidence(self):
        """Test that default confidence is 1.0."""
        recommendation = WeatherRecommendation(
            forecast=self.forecast,
            recommendation=FootwearRecommendation.SHOE,
            reason="Test"
        )
        assert recommendation.confidence == 1.0
