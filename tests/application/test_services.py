"""Unit tests for application services."""

import pytest
from datetime import datetime

from src.application.services import RainBasedRecommendationService
from src.domain.models import (
    Location,
    WeatherForecast,
    FootwearRecommendation,
)
from src.domain.exceptions import RecommendationException


class TestRainBasedRecommendationService:
    """Tests for RainBasedRecommendationService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.location = Location(latitude=23.8103, longitude=90.4125, name="Dhaka")

    def test_service_initialization_with_default_threshold(self):
        """Test service initializes with default threshold of 30%."""
        service = RainBasedRecommendationService()
        assert service._rain_threshold == 30

    def test_service_initialization_with_custom_threshold(self):
        """Test service initializes with custom threshold."""
        service = RainBasedRecommendationService(rain_threshold=50)
        assert service._rain_threshold == 50

    def test_invalid_threshold_too_high(self):
        """Test that threshold > 100 raises ValueError."""
        with pytest.raises(ValueError, match="Invalid rain threshold"):
            RainBasedRecommendationService(rain_threshold=101)

    def test_invalid_threshold_negative(self):
        """Test that negative threshold raises ValueError."""
        with pytest.raises(ValueError, match="Invalid rain threshold"):
            RainBasedRecommendationService(rain_threshold=-1)

    def test_recommend_sandals_when_rain_above_threshold(self):
        """Test recommends sandals when rain probability >= threshold."""
        service = RainBasedRecommendationService(rain_threshold=30)
        forecast = WeatherForecast(
            rain_probability=40,
            temperature=25,
            humidity=70,
            condition="Cloudy",
            timestamp=datetime.now(),
            location=self.location
        )

        recommendation = service.recommend(forecast)

        assert recommendation.recommendation == FootwearRecommendation.SANDAL
        assert recommendation.forecast == forecast
        assert "40%" in recommendation.reason
        assert 0 <= recommendation.confidence <= 1

    def test_recommend_shoes_when_rain_below_threshold(self):
        """Test recommends shoes when rain probability < threshold."""
        service = RainBasedRecommendationService(rain_threshold=30)
        forecast = WeatherForecast(
            rain_probability=10,
            temperature=25,
            humidity=50,
            condition="Clear sky",
            timestamp=datetime.now(),
            location=self.location
        )

        recommendation = service.recommend(forecast)

        assert recommendation.recommendation == FootwearRecommendation.SHOE
        assert recommendation.forecast == forecast
        assert "10%" in recommendation.reason
        assert 0 <= recommendation.confidence <= 1

    def test_recommend_sandals_at_exact_threshold(self):
        """Test recommends sandals when rain probability equals threshold."""
        service = RainBasedRecommendationService(rain_threshold=30)
        forecast = WeatherForecast(
            rain_probability=30,
            temperature=25,
            humidity=65,
            condition="Overcast",
            timestamp=datetime.now(),
            location=self.location
        )

        recommendation = service.recommend(forecast)

        assert recommendation.recommendation == FootwearRecommendation.SANDAL
        assert recommendation.forecast == forecast

    def test_recommend_shoes_just_below_threshold(self):
        """Test recommends shoes when rain probability is just below threshold."""
        service = RainBasedRecommendationService(rain_threshold=30)
        forecast = WeatherForecast(
            rain_probability=29,
            temperature=25,
            humidity=60,
            condition="Partly cloudy",
            timestamp=datetime.now(),
            location=self.location
        )

        recommendation = service.recommend(forecast)

        assert recommendation.recommendation == FootwearRecommendation.SHOE

    def test_recommend_with_zero_rain_probability(self):
        """Test recommendation with 0% rain probability."""
        service = RainBasedRecommendationService(rain_threshold=30)
        forecast = WeatherForecast(
            rain_probability=0,
            temperature=30,
            humidity=40,
            condition="Clear sky",
            timestamp=datetime.now(),
            location=self.location
        )

        recommendation = service.recommend(forecast)

        assert recommendation.recommendation == FootwearRecommendation.SHOE
        assert recommendation.confidence == 1.0  # High confidence for clear day

    def test_recommend_with_high_rain_probability(self):
        """Test recommendation with 100% rain probability."""
        service = RainBasedRecommendationService(rain_threshold=30)
        forecast = WeatherForecast(
            rain_probability=100,
            temperature=22,
            humidity=95,
            condition="Heavy rain",
            timestamp=datetime.now(),
            location=self.location
        )

        recommendation = service.recommend(forecast)

        assert recommendation.recommendation == FootwearRecommendation.SANDAL
        assert recommendation.confidence == 1.0  # High confidence for certain rain

    def test_recommend_adjusts_reason_when_actually_raining(self):
        """Test that reason includes weather condition when it's raining."""
        service = RainBasedRecommendationService(rain_threshold=30)
        forecast = WeatherForecast(
            rain_probability=50,
            temperature=24,
            humidity=85,
            condition="Light rain",
            timestamp=datetime.now(),
            location=self.location
        )

        recommendation = service.recommend(forecast)

        assert recommendation.recommendation == FootwearRecommendation.SANDAL
        assert "Light rain" in recommendation.reason

    def test_recommend_with_different_thresholds(self):
        """Test that different thresholds produce different recommendations."""
        forecast = WeatherForecast(
            rain_probability=40,
            temperature=25,
            humidity=70,
            condition="Cloudy",
            timestamp=datetime.now(),
            location=self.location
        )

        # With threshold 30%, should recommend sandals
        service_low = RainBasedRecommendationService(rain_threshold=30)
        recommendation_low = service_low.recommend(forecast)
        assert recommendation_low.recommendation == FootwearRecommendation.SANDAL

        # With threshold 50%, should recommend shoes
        service_high = RainBasedRecommendationService(rain_threshold=50)
        recommendation_high = service_high.recommend(forecast)
        assert recommendation_high.recommendation == FootwearRecommendation.SHOE

    def test_confidence_is_between_zero_and_one(self):
        """Test that confidence is always between 0 and 1."""
        service = RainBasedRecommendationService(rain_threshold=30)

        test_probabilities = [0, 10, 25, 30, 50, 75, 100]

        for rain_prob in test_probabilities:
            forecast = WeatherForecast(
                rain_probability=rain_prob,
                temperature=25,
                humidity=60,
                condition="Test",
                timestamp=datetime.now(),
                location=self.location
            )
            recommendation = service.recommend(forecast)
            assert 0 <= recommendation.confidence <= 1, \
                f"Confidence {recommendation.confidence} not in [0,1] for rain_prob={rain_prob}%"
