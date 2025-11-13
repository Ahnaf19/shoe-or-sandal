"""
Application services - Business logic implementation.

Services implement business rules and coordinate domain objects.
"""

import logging
from typing import Protocol

from src.domain.models import (
    FootwearRecommendation,
    WeatherForecast,
    WeatherRecommendation,
)
from src.domain.exceptions import RecommendationException

logger = logging.getLogger(__name__)


class RecommendationStrategy(Protocol):
    """Protocol for recommendation strategies (Strategy Pattern)."""

    def recommend(self, forecast: WeatherForecast) -> WeatherRecommendation:
        """Generate recommendation based on weather forecast."""
        ...


class RainBasedRecommendationService:
    """
    Service that generates footwear recommendations based on rain probability.

    Implements Single Responsibility Principle - only handles recommendation logic.
    """

    def __init__(self, rain_threshold: int = 30) -> None:
        """
        Initialize recommendation service.

        Args:
            rain_threshold: Rain probability threshold (%) for sandal recommendation
        """
        if not 0 <= rain_threshold <= 100:
            raise ValueError(f"Invalid rain threshold: {rain_threshold}")

        self._rain_threshold = rain_threshold
        logger.info(f"Initialized RainBasedRecommendationService with threshold={rain_threshold}%")

    def recommend(self, forecast: WeatherForecast) -> WeatherRecommendation:
        """
        Generate footwear recommendation based on weather forecast.

        Business Rules:
        - If rain probability >= threshold → recommend sandals
        - Otherwise → recommend shoes
        - Consider actual rain conditions for higher confidence

        Args:
            forecast: Weather forecast data

        Returns:
            WeatherRecommendation with suggested footwear

        Raises:
            RecommendationException: If unable to generate recommendation
        """
        try:
            rain_prob = forecast.rain_probability
            is_rainy = forecast.is_rainy()

            if rain_prob >= self._rain_threshold:
                recommendation = FootwearRecommendation.SANDAL
                reason = f"Rain probability is {rain_prob}% (threshold: {self._rain_threshold}%)"
                confidence = self._calculate_confidence(rain_prob, is_rainy, True)
            else:
                recommendation = FootwearRecommendation.SHOE
                reason = f"Rain probability is only {rain_prob}% (threshold: {self._rain_threshold}%)"
                confidence = self._calculate_confidence(rain_prob, is_rainy, False)

            # Adjust reason if actually raining
            if is_rainy:
                reason += f" and weather indicates rain ({forecast.condition})"

            logger.info(
                f"Generated recommendation: {recommendation.value} "
                f"(rain={rain_prob}%, confidence={confidence:.2f})"
            )

            return WeatherRecommendation(
                forecast=forecast,
                recommendation=recommendation,
                reason=reason,
                confidence=confidence,
            )

        except Exception as e:
            logger.error(f"Failed to generate recommendation: {e}")
            raise RecommendationException(f"Unable to generate recommendation: {e}") from e

    def _calculate_confidence(
        self, rain_prob: int, is_rainy: bool, recommend_sandal: bool
    ) -> float:
        """
        Calculate confidence level for recommendation.

        Higher confidence when:
        - Rain probability is very high or very low (clear decision)
        - Weather condition matches rain probability
        - Recommendation aligns with actual conditions

        Args:
            rain_prob: Rain probability percentage
            is_rainy: Whether conditions indicate rain
            recommend_sandal: Whether recommending sandals

        Returns:
            Confidence score between 0 and 1
        """
        # Base confidence from probability certainty
        if recommend_sandal:
            # Higher confidence as probability increases above threshold
            base_confidence = min(1.0, (rain_prob - self._rain_threshold) / (100 - self._rain_threshold))
            base_confidence = max(0.5, base_confidence)  # Minimum 50% confidence
        else:
            # Higher confidence as probability decreases below threshold
            base_confidence = min(1.0, (self._rain_threshold - rain_prob) / self._rain_threshold)
            base_confidence = max(0.5, base_confidence)

        # Boost confidence if weather condition aligns with recommendation
        if (recommend_sandal and is_rainy) or (not recommend_sandal and not is_rainy):
            base_confidence = min(1.0, base_confidence * 1.2)

        return round(base_confidence, 2)


class MessageFormatter:
    """
    Service for formatting messages for notifications.

    Implements Single Responsibility Principle - only handles message formatting.
    """

    @staticmethod
    def format_weather_recommendation(recommendation: WeatherRecommendation) -> str:
        """
        Format weather recommendation as a readable message.

        Args:
            recommendation: WeatherRecommendation to format

        Returns:
            Formatted message string with markdown
        """
        forecast = recommendation.forecast
        rec = recommendation.recommendation

        # Choose emoji based on weather
        weather_emoji = MessageFormatter._get_weather_emoji(
            forecast.rain_probability, forecast.condition
        )

        # Choose recommendation emoji
        rec_emoji = "👡" if rec == FootwearRecommendation.SANDAL else "👞"

        message = f"""*Weather Update for {forecast.location.name}* {weather_emoji}

*Condition:* {forecast.condition}
*Rain Probability:* {forecast.rain_probability}%
*Temperature:* {forecast.temperature}°C
*Humidity:* {forecast.humidity}%

*Recommendation:* Wear *{rec.value}s* today! {rec_emoji}
*Reason:* {recommendation.reason}
*Confidence:* {int(recommendation.confidence * 100)}%

_Stay comfortable!_"""

        return message

    @staticmethod
    def _get_weather_emoji(rain_probability: int, condition: str) -> str:
        """Determine appropriate weather emoji."""
        if rain_probability >= 70 or "storm" in condition.lower():
            return "🌧️"
        elif rain_probability >= 30 or "rain" in condition.lower():
            return "⛅"
        elif "cloud" in condition.lower():
            return "☁️"
        elif "snow" in condition.lower():
            return "❄️"
        elif "fog" in condition.lower():
            return "🌫️"
        else:
            return "☀️"

    @staticmethod
    def format_error_message(error: Exception) -> str:
        """
        Format error as user-friendly message.

        Args:
            error: Exception that occurred

        Returns:
            Formatted error message
        """
        message = f"""⚠️ *Weather Bot Error*

An error occurred while processing your weather update:

*Error:* {str(error)}

Please check the logs for more details."""

        return message
