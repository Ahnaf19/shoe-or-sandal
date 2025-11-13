"""
Domain exceptions - Business logic errors.

These exceptions represent business rule violations and error conditions.
"""


class DomainException(Exception):
    """Base exception for all domain errors."""

    def __init__(self, message: str, *args: object) -> None:
        super().__init__(message, *args)
        self.message = message


class WeatherDataException(DomainException):
    """Raised when weather data is invalid or unavailable."""

    pass


class LocationException(DomainException):
    """Raised when location data is invalid."""

    pass


class RecommendationException(DomainException):
    """Raised when unable to generate recommendation."""

    pass


class ConfigurationException(DomainException):
    """Raised when configuration is invalid or missing."""

    pass


class NotificationException(DomainException):
    """Raised when notification delivery fails."""

    pass


class PersistenceException(DomainException):
    """Raised when data persistence operations fail."""

    pass


class ExternalServiceException(DomainException):
    """Raised when external service calls fail."""

    def __init__(self, service_name: str, message: str, *args: object) -> None:
        super().__init__(f"{service_name}: {message}", *args)
        self.service_name = service_name
