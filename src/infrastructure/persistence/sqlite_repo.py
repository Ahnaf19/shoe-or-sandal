"""
SQLite weather repository implementation.

Concrete implementation of WeatherRepository using SQLite database.
"""

import logging
import sqlite3
from contextlib import contextmanager
from datetime import date
from pathlib import Path
from typing import List, Optional, Generator

from src.domain.models import (
    FootwearRecommendation,
    Location,
    WeatherRecord,
    WeatherStatistics,
)
from src.domain.repositories import WeatherRepository
from src.domain.exceptions import PersistenceException

logger = logging.getLogger(__name__)


class SQLiteWeatherRepository(WeatherRepository):
    """
    Weather repository using SQLite for persistence.

    Provides thread-safe database operations with proper connection management.
    Implements the Repository pattern for data access.
    """

    # Database schema version for migrations
    SCHEMA_VERSION = 1

    def __init__(self, db_path: str) -> None:
        """
        Initialize SQLite repository.

        Args:
            db_path: Path to SQLite database file

        Raises:
            PersistenceException: If unable to initialize database
        """
        self._db_path = db_path
        logger.info(f"Initializing SQLiteWeatherRepository at {db_path}")

        try:
            self._ensure_database_exists()
            self._initialize_schema()
            logger.info("SQLite repository initialized successfully")
        except Exception as e:
            error_msg = f"Failed to initialize database: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PersistenceException(error_msg) from e

    @contextmanager
    def _get_connection(self) -> Generator[sqlite3.Connection, None, None]:
        """
        Context manager for database connections.

        Ensures connections are properly closed and transactions are handled.

        Yields:
            Database connection

        Raises:
            PersistenceException: If connection fails
        """
        conn = None
        try:
            conn = sqlite3.connect(self._db_path)
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
            conn.commit()
        except sqlite3.Error as e:
            if conn:
                conn.rollback()
            error_msg = f"Database error: {str(e)}"
            logger.error(error_msg)
            raise PersistenceException(error_msg) from e
        finally:
            if conn:
                conn.close()

    def _ensure_database_exists(self) -> None:
        """Ensure database directory exists."""
        db_file = Path(self._db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)

    def _initialize_schema(self) -> None:
        """Create database tables if they don't exist."""
        with self._get_connection() as conn:
            # Main weather history table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS weather_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE UNIQUE NOT NULL,
                    rain_probability INTEGER NOT NULL CHECK(rain_probability >= 0 AND rain_probability <= 100),
                    actual_rained BOOLEAN NOT NULL CHECK(actual_rained IN (0, 1)),
                    temperature REAL NOT NULL,
                    humidity REAL NOT NULL CHECK(humidity >= 0 AND humidity <= 100),
                    weather_condition TEXT NOT NULL,
                    recommendation TEXT NOT NULL CHECK(recommendation IN ('sandal', 'shoe')),
                    location_name TEXT NOT NULL,
                    location_latitude REAL NOT NULL,
                    location_longitude REAL NOT NULL,
                    raw_data TEXT,
                    message_sent_at TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Indices for common queries
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_date ON weather_history(date)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_actual_rained ON weather_history(actual_rained)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_rain_probability ON weather_history(rain_probability)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_recommendation ON weather_history(recommendation)"
            )

            # Schema version tracking
            conn.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)

            # Insert initial version if not exists
            conn.execute(
                "INSERT OR IGNORE INTO schema_version (version) VALUES (?)",
                (self.SCHEMA_VERSION,),
            )

            logger.debug("Database schema initialized")

    def save(self, record: WeatherRecord) -> bool:
        """
        Persist a weather record.

        Uses INSERT OR REPLACE to handle duplicates by date.

        Args:
            record: WeatherRecord to save

        Returns:
            True if saved successfully

        Raises:
            PersistenceException: If unable to save
        """
        logger.debug(f"Saving weather record for {record.date}")

        try:
            with self._get_connection() as conn:
                conn.execute(
                    """
                    INSERT OR REPLACE INTO weather_history
                    (date, rain_probability, actual_rained, temperature, humidity,
                     weather_condition, recommendation, location_name, location_latitude,
                     location_longitude, raw_data, message_sent_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        record.date.isoformat(),
                        record.rain_probability,
                        1 if record.actual_rained else 0,
                        record.temperature,
                        record.humidity,
                        record.weather_condition,
                        record.recommendation.value,
                        record.location.name,
                        record.location.latitude,
                        record.location.longitude,
                        record.raw_data,
                        record.message_sent_at.isoformat() if record.message_sent_at else None,
                    ),
                )

            logger.info(f"Saved weather record for {record.date}")
            return True

        except Exception as e:
            error_msg = f"Failed to save weather record: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise PersistenceException(error_msg) from e

    def find_by_date(self, record_date: date) -> Optional[WeatherRecord]:
        """
        Retrieve weather record for a specific date.

        Args:
            record_date: Date to search for

        Returns:
            WeatherRecord if found, None otherwise
        """
        logger.debug(f"Finding weather record for {record_date}")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM weather_history WHERE date = ?",
                    (record_date.isoformat(),),
                )
                row = cursor.fetchone()

                if row:
                    logger.debug(f"Found weather record for {record_date}")
                    return self._row_to_record(row)
                else:
                    logger.debug(f"No record found for {record_date}")
                    return None

        except Exception as e:
            error_msg = f"Failed to find weather record: {str(e)}"
            logger.error(error_msg)
            raise PersistenceException(error_msg) from e

    def find_all(self) -> List[WeatherRecord]:
        """
        Retrieve all weather records.

        Returns:
            List of all WeatherRecord objects, ordered by date descending
        """
        logger.debug("Retrieving all weather records")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT * FROM weather_history ORDER BY date DESC"
                )
                rows = cursor.fetchall()

                records = [self._row_to_record(row) for row in rows]
                logger.info(f"Retrieved {len(records)} weather records")
                return records

        except Exception as e:
            error_msg = f"Failed to retrieve weather records: {str(e)}"
            logger.error(error_msg)
            raise PersistenceException(error_msg) from e

    def get_statistics(self) -> WeatherStatistics:
        """
        Calculate statistics from stored records.

        Returns:
            WeatherStatistics with aggregated data
        """
        logger.debug("Calculating weather statistics")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute("""
                    SELECT
                        COUNT(*) as total_days,
                        SUM(CASE WHEN actual_rained = 1 THEN 1 ELSE 0 END) as rainy_days,
                        AVG(rain_probability) as avg_rain_probability,
                        AVG(temperature) as avg_temperature,
                        SUM(CASE WHEN recommendation = 'sandal' THEN 1 ELSE 0 END) as sandal_count,
                        SUM(CASE WHEN recommendation = 'shoe' THEN 1 ELSE 0 END) as shoe_count
                    FROM weather_history
                """)

                row = cursor.fetchone()

                stats = WeatherStatistics(
                    total_days=row["total_days"] or 0,
                    rainy_days=row["rainy_days"] or 0,
                    average_rain_probability=round(row["avg_rain_probability"] or 0, 2),
                    average_temperature=round(row["avg_temperature"] or 0, 2),
                    sandal_recommendations=row["sandal_count"] or 0,
                    shoe_recommendations=row["shoe_count"] or 0,
                )

                logger.info(
                    f"Statistics: {stats.total_days} days, "
                    f"{stats.rainy_days} rainy days"
                )

                return stats

        except Exception as e:
            error_msg = f"Failed to calculate statistics: {str(e)}"
            logger.error(error_msg)
            raise PersistenceException(error_msg) from e

    def count_rainy_days(self) -> int:
        """
        Count number of days that actually rained.

        Returns:
            Number of rainy days
        """
        logger.debug("Counting rainy days")

        try:
            with self._get_connection() as conn:
                cursor = conn.execute(
                    "SELECT COUNT(*) FROM weather_history WHERE actual_rained = 1"
                )
                count = cursor.fetchone()[0]

                logger.info(f"Found {count} rainy days")
                return count

        except Exception as e:
            error_msg = f"Failed to count rainy days: {str(e)}"
            logger.error(error_msg)
            raise PersistenceException(error_msg) from e

    def _row_to_record(self, row: sqlite3.Row) -> WeatherRecord:
        """
        Convert database row to WeatherRecord domain object.

        Args:
            row: SQLite row

        Returns:
            WeatherRecord instance
        """
        from datetime import datetime

        location = Location(
            latitude=row["location_latitude"],
            longitude=row["location_longitude"],
            name=row["location_name"],
        )

        return WeatherRecord(
            id=row["id"],
            date=date.fromisoformat(row["date"]),
            rain_probability=row["rain_probability"],
            actual_rained=bool(row["actual_rained"]),
            temperature=row["temperature"],
            humidity=row["humidity"],
            weather_condition=row["weather_condition"],
            recommendation=FootwearRecommendation(row["recommendation"]),
            location=location,
            raw_data=row["raw_data"],
            message_sent_at=(
                datetime.fromisoformat(row["message_sent_at"])
                if row["message_sent_at"]
                else None
            ),
            created_at=(
                datetime.fromisoformat(row["created_at"]) if row["created_at"] else None
            ),
        )
