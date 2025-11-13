# 👞 Shoe or Sandal Bot 👡

A weather-based footwear recommendation bot that sends daily Telegram notifications. Helps you decide whether to wear shoes or sandals based on rain probability in your location.

Built with **Clean Architecture** and **SOLID principles** to demonstrate proper software design patterns in a practical application. The bot collects weather data for potential ML training while solving a real daily decision-making problem.

> **Status:** Core weather-to-Telegram pipeline implemented. Daily scheduling planned for future releases.

## Features

- **Daily Weather Updates**: Get weather forecasts for Dhaka every morning at 8 AM (Scheduler coming soon!)
- **Smart Recommendations**: Suggests sandals when rain probability ≥ 30%, shoes otherwise
- **Telegram Notifications**: Receives formatted weather updates via Telegram
- **ML Dataset Collection**: Automatically stores weather data when it rains or rain is likely
- **Clean Architecture**: Follows SOLID principles with clear separation of concerns

## Tech Stack

- **Python 3.10+**
- **Clean Architecture** with layered design
- **Open-Meteo API**: Free weather forecasts (no API key required)
- **Telegram Bot API**: Simple HTTP-based messaging
- **SQLite**: Local database for weather history
- **Type Hints**: Full type annotations for better IDE support

### Architecture Layers

This project follows **Clean Architecture** with 4 distinct layers:

- **Domain Layer**: Core business logic (no external dependencies)
- **Application Layer**: Use cases and business workflows
- **Infrastructure Layer**: External service implementations (API, Database, Telegram)
- **Presentation Layer**: CLI and configuration

**For detailed architecture diagrams, dependency flows, and SOLID principles implementation, see [ARCHITECTURE.md](ARCHITECTURE.md)**

## Quick Start

### 1. Prerequisites

- Python 3.10 or higher
- A Telegram account
- `uv` or `pip` for package management

### 2. Clone and Install Dependencies

```bash
git clone <your-repo-url>
cd shoe-or-sandal

# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

### 3. Set Up Telegram Bot

#### Create a Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Choose a name: "Weather Reminder Bot"
4. Choose a username (must end in 'bot'): `dhaka_weather_reminder_bot`
5. Copy the bot token provided

#### Get Your Chat ID

1. Send any message to your bot
2. Visit: `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates`
3. Find `"chat":{"id":123456789}` in the JSON response
4. Copy your chat ID

### 4. Configure Environment Variables

```bash
# Copy the example env file
cp .env.example .env

# Edit .env with your credentials
nano .env  # or use your preferred editor
```

Update `.env` with your Telegram credentials:

```env
TELEGRAM_BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
TELEGRAM_CHAT_ID=123456789
```

### 5. Test the Bot

```bash
python main.py
```

You should receive a weather message on Telegram!

## Configuration

All configuration is done via `.env` file. See `.env.example` for all available options:

### Required Settings

- `TELEGRAM_BOT_TOKEN`: Your bot token from BotFather
- `TELEGRAM_CHAT_ID`: Your Telegram chat ID

### Location Settings

- `LOCATION_NAME`: Location display name (default: "Dhaka")
- `LOCATION_LATITUDE`: Latitude
- `LOCATION_LONGITUDE`: Longitude
- `TIMEZONE`: IANA timezone (default: "Asia/Dhaka")

### Weather Settings

- `RAIN_THRESHOLD`: Rain probability % for sandal recommendation (default: 30)
- `WEATHER_API_TIMEOUT`: API timeout in seconds (default: 10)
- `WEATHER_API_MAX_RETRIES`: Max retry attempts (default: 3)

### Database Settings

- `DATABASE_PATH`: SQLite database path (default: "weather_history.db")

### Logging Settings

- `LOG_LEVEL`: Log level (default: "INFO")
- `LOG_FORMAT`: Python logging format string
- `LOG_FILE`: Optional log file path

## Code Hardening Features

✅ **Type Safety**: Full type hints throughout codebase
✅ **Error Handling**: Custom exceptions for different error types
✅ **Retry Logic**: Exponential backoff for external service calls
✅ **Timeouts**: Configurable timeouts to prevent hanging
✅ **Validation**: Input validation at system boundaries
✅ **Logging**: Comprehensive logging at all levels
✅ **Health Checks**: System health verification before execution
✅ **Separation of Concerns**: Clear layer boundaries
✅ **Testability**: Interface-based design for easy mocking
✅ **Configuration Validation**: Fail fast on invalid configuration

## ML Dataset Collection

The bot automatically collects weather data when:

- Rain probability ≥ threshold (default 30%), OR
- It's actually raining

### Database Schema

```sql
weather_history (
    id, date, rain_probability, actual_rained,
    temperature, humidity, weather_condition,
    recommendation, location_name, location_latitude,
    location_longitude, raw_data, message_sent_at,
    created_at, updated_at
)
```

### Accessing Your Dataset

```python
from src.infrastructure.persistence.sqlite_repo import SQLiteWeatherRepository

repo = SQLiteWeatherRepository("weather_history.db")

# Get all records
records = repo.find_all()

# Get statistics
stats = repo.get_statistics()
print(f"Total days: {stats.total_days}")
print(f"Rainy days: {stats.rainy_days}")

# Export for ML training
import pandas as pd
df = pd.DataFrame([record.to_dict() for record in records])
df.to_csv('weather_dataset.csv', index=False)
```

## API Rate Limits

- **Open-Meteo**: 10,000 calls/day
- **Telegram**: 30 messages/second

## Architecture Benefits

### Why Clean Architecture?

1. **Testability**: Business logic can be tested without external dependencies
2. **Flexibility**: Easy to swap implementations (different databases, APIs, etc.)
3. **Maintainability**: Clear separation of concerns makes code easier to understand
4. **Scalability**: New features can be added without breaking existing code
5. **Independence**: Business rules don't depend on frameworks or UI

### Example: Swapping Weather Providers

```python
# Easy to switch from Open-Meteo to another provider
# Old: OpenMeteoWeatherProvider
# New: YourCustomWeatherProvider

weather_provider = YourCustomWeatherProvider()
# Rest of the code remains unchanged!
```

## Future Enhancements

At least, would try to complete the listed features. :)

**Features:**

- [x] Automated weather-to-Telegram Alert Pipeline
- [ ] Scheduled daily alerts (cron/cloud deployment)
- [ ] Multi-location support (track weather for multiple locations/cities)

**Infrastructure:**

- [ ] Docker containerization with docker-compose
- [ ] Async/await for concurrent API operations
- [ ] Web dashboard (FastAPI) to visualize weather history and ML datasets
- [ ] Alternative notification channels (SMS, Email, Discord, Slack)
- [ ] Message queue (Redis/RabbitMQ) for reliability
- [ ] PostgreSQL migration from SQLite for production scale

**Operations:**

- [ ] Monitoring and observability (Prometheus metrics, health endpoints)
- [ ] Database migrations system (Alembic)
- [ ] Performance optimization and caching (Redis)
- [ ] Automated backups for weather dataset
- [ ] Graceful error handling and retry mechanisms

**Testing & Quality:**

- [x] Unit tests with pytest (domain & application layers)
- [ ] Integration tests with mocked infrastructure
- [ ] End-to-end tests with test Telegram account
- [ ] Code coverage reporting (pytest-cov, target: >80%)
- [ ] Type checking with mypy
- [ ] Linting with ruff/black for code consistency
- [ ] CI/CD pipeline with GitHub Actions
- [ ] Pre-commit hooks for code quality checks

## Contributing

This is a **hobby project** demonstrating Clean Architecture and SOLID principles. Contributions are welcome!

**How to Contribute:**

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Follow the existing architecture patterns (see [ARCHITECTURE.md](ARCHITECTURE.md))
4. Write tests for new functionality
5. Ensure code follows type hints and documentation standards
6. Submit a pull request

you can take inspiration from the above ## Future Enhancements section.

**Contribution Ideas:**

- **Testing**: Add pytest tests, implement code coverage, set up CI/CD
- **New Providers**: Implement alternative weather APIs (WeatherAPI, OpenWeatherMap, AccuWeather)
- **Notifications**: Add SMS (Twilio), Email (SendGrid), Discord, or Slack integrations
- **ML/Analytics**: Train prediction models, build trend analysis, create data visualizations
- **Web Dashboard**: Build FastAPI interface with historical data and dataset exports
- **Infrastructure**: Dockerize the app, add async operations, implement message queues
- **Documentation**: Add API docs, create video tutorials, write deployment guides

## License

MIT License - feel free to use and modify!

## Acknowledgments

- Weather data from [Open-Meteo](https://open-meteo.com/)
- Telegram Bot API for messaging
- Inspired by the daily struggle of choosing appropriate footwear
- All hail Claude Sonnet 4.5!

---

**Enjoy your daily weather reminders and happy ML dataset collection!**
