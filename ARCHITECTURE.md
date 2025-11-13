# Architecture Documentation

This project implements **Clean Architecture** (Uncle Bob's layered approach) where dependencies point inward toward business logic. External concerns (APIs, databases, UI) are isolated in outer layers, making the core domain independent, testable, and maintainable.

**Key Principles:**
- **Dependency Rule**: Inner layers never depend on outer layers
- **Domain-Centric**: Business logic has zero external dependencies
- **Interface Segregation**: Small, focused contracts (ports) between layers
- **Dependency Inversion**: High-level modules depend on abstractions, not implementations
- **Single Responsibility**: Each component has one reason to change

---

## High-Level Overview

```
┌─────────────────────────────────────────────────────────┐
│                   USER / SCHEDULER                      │
│                  (runs: python main.py)                 │
└────────────────────────┬────────────────────────────────┘
                         │
                    ┌────▼─────┐
                    │  main.py │  Entry point
                    └────┬─────┘
                         │
        ┏━━━━━━━━━━━━━━━━▼━━━━━━━━━━━━━━━━┓
        ┃     CLEAN ARCHITECTURE LAYERS   ┃
        ┃                                 ┃
        ┃  ┌────────────────────────────┐ ┃
        ┃  │  Presentation (CLI/Config) │ ┃  Handles I/O, DI
        ┃  └──────────┬─────────────────┘ ┃
        ┃             │                   ┃
        ┃  ┌──────────▼─────────────────┐ ┃
        ┃  │  Application (Use Cases)   │ ┃  Business workflows
        ┃  └──────────┬─────────────────┘ ┃
        ┃             │                   ┃
        ┃  ┌──────────▼─────────────────┐ ┃
        ┃  │  Domain (Business Logic)   │ ┃  Core entities
        ┃  │     [NO DEPENDENCIES]      │ ┃  Pure business rules
        ┃  └──────────▲─────────────────┘ ┃
        ┃             │ implements        ┃
        ┃  ┌──────────┴─────────────────┐ ┃
        ┃  │  Infrastructure (Adapters) │ ┃  External services
        ┃  └──────────┬─────────────────┘ ┃
        ┃             │                   ┃
        ┗━━━━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━━┛
                      │
         ┌────────────┼────────────┐
         │            │            │
    ┌────▼───┐   ┌────▼────┐  ┌───▼────┐
    │Weather │   │Telegram │  │SQLite  │  External systems
    │  API   │   │   Bot   │  │   DB   │
    └────────┘   └─────────┘  └────────┘
```

**Why?** Dependencies point inward. Business logic never depends on external services.

---

## Layer Diagram: Dependency Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  PRESENTATION LAYER (src/presentation/)                         │
│  ┌──────────────┐  ┌────────────────┐                           │
│  │  config.py   │  │    cli.py      │  Entry & Configuration    │
│  │  (AppConfig) │  │ (Dependency    │  - Loads .env             │
│  │              │  │  Injection)    │  - Wires up services      │
│  └──────────────┘  └────────┬───────┘  - Logging setup          │
└──────────────────────────────┼──────────────────────────────────┘
                               │ calls
┌──────────────────────────────▼──────────────────────────────────┐
│  APPLICATION LAYER (src/application/)                           │
│  ┌────────────────────────────────────────────────┐             │
│  │  use_cases.py                                  │             │
│  │  • SendWeatherReminderUseCase ←── Main flow    │             │
│  │  • GetWeatherStatisticsUseCase                 │             │
│  │  • VerifySystemHealthUseCase                   │             │
│  └───────────────────┬────────────────────────────┘             │
│                      │ uses                                     │
│  ┌───────────────────▼────────────────────────────┐             │
│  │  services.py                                   │             │
│  │  • RainBasedRecommendationService (logic)      │             │
│  │  • MessageFormatter (formatting)               │             │
│  └────────────────────────────────────────────────┘             │
└──────────────────────────────┬──────────────────────────────────┘
                               │ depends on
┌──────────────────────────────▼──────────────────────────────────┐
│  DOMAIN LAYER (src/domain/) ★ CORE ★                            │
│  ┌────────────────┐  ┌─────────────────┐  ┌──────────────────┐  │
│  │  models.py     │  │ repositories.py │  │ exceptions.py    │  │
│  │                │  │                 │  │                  │  │
│  │ • Location     │  │ • WeatherProvider      (interfaces)   │  │
│  │ • Weather      │  │ • NotificationService  (ports)        │  │
│  │   Forecast     │  │ • WeatherRepository                   │  │
│  │ • Weather      │  │                 │  │ • DomainException│  │
│  │   Record       │  │ [Abstractions]  │  │ • WeatherData    │  │
│  │                │  │                 │  │   Exception      │  │
│  └────────────────┘  └─────────────────┘  └──────────────────┘  │
│                                                                 │
│  NO EXTERNAL DEPENDENCIES - Pure Python, fully testable         │
└──────────────────────────────▲──────────────────────────────────┘
                               │ implements (Dependency Inversion)
┌──────────────────────────────┴──────────────────────────────────┐
│  INFRASTRUCTURE LAYER (src/infrastructure/)                     │
│                                                                 │
│  ┌──────────────────┐  ┌─────────────────┐  ┌───────────────┐   │
│  │  weather/        │  │  messaging/     │  │ persistence/  │   │
│  │  open_meteo.py   │  │  telegram.py    │  │ sqlite_repo.py│   │
│  │                  │  │                 │  │               │   │
│  │ OpenMeteo        │  │ Telegram        │  │ SQLite        │   │
│  │ WeatherProvider  │  │ Notification    │  │ Weather       │   │
│  │                  │  │ Service         │  │ Repository    │   │
│  │ implements       │  │ implements      │  │ implements    │   │
│  │ WeatherProvider  │  │ Notification    │  │ Weather       │   │
│  │ interface        │  │ Service         │  │ Repository    │   │
│  └────────┬─────────┘  └────────┬────────┘  └───────┬───────┘   │
└───────────┼────────────────────┼────────────────────┼───────────┘
            │                    │                    │
            │ HTTP               │ HTTP               │ SQL
            │                    │                    │
    ┌───────▼────────┐   ┌───────▼────────┐   ┌──────▼───────┐
    │ Open-Meteo API │   │ Telegram Bot   │   │ SQLite DB    │
    │ api.open-      │   │ api.telegram.  │   │ weather_     │
    │ meteo.com      │   │ org            │   │ history.db   │
    └────────────────┘   └────────────────┘   └──────────────┘
```

**Why?** Interfaces (ports) in domain are implemented by infrastructure (adapters).
Swapping Telegram for SMS or SQLite for Postgres requires zero domain/application changes.

---

## Execution Flow: What Happens If Run the Bot

```
1. ENTRY
   main.py
     │
     └──> cli.main()
          │
          ├─ Load .env file
          ├─ Create AppConfig
          └─ Initialize CLI

2. DEPENDENCY INJECTION
   cli.py
     │
     ├─ weather_provider = OpenMeteoWeatherProvider()
     ├─ notification_service = TelegramNotificationService()
     ├─ weather_repository = SQLiteWeatherRepository()
     ├─ recommendation_service = RainBasedRecommendationService()
     └─ message_formatter = MessageFormatter()

3. HEALTH CHECK
   VerifySystemHealthUseCase.execute()
     │
     ├─ Test weather API      [✓ OK]
     ├─ Test Telegram bot     [✓ OK]
     └─ Test database         [✓ OK]

4. MAIN WORKFLOW
   SendWeatherReminderUseCase.execute(location)
     │
     ├─ STEP 1: Fetch Weather
     │   weather_provider.get_morning_forecast(location)
     │     │
     │     └──> HTTP GET: api.open-meteo.com
     │          Returns: WeatherForecast(rain=0%, temp=23.8°C)
     │
     ├─ STEP 2: Generate Recommendation
     │   recommendation_service.recommend(forecast)
     │     │
     │     └──> Business Logic:
     │          rain < 30% threshold → SHOE 👞
     │
     ├─ STEP 3: Format Message
     │   message_formatter.format_weather_recommendation(...)
     │     │
     │     └──> "☀️ Good Morning! ... Wear shoes today!"
     │
     ├─ STEP 4: Send Notification
     │   notification_service.send_message(message)
     │     │
     │     └──> HTTP POST: api.telegram.org/botXXX/sendMessage
     │          Returns: message_id=4
     │
     └─ STEP 5: Store Data (conditional)
         if rain >= 30% or is_raining:
             weather_repository.save(record)
         else:
             skip (ML dataset only collects rain data)

5. RESULT
   └─ Success: True
      Message Sent: True
      Data Saved: False (no rain)
```

---

## File Structure with Responsibilities

```
shoe-or-sandal/
│
├── main.py                          Entry point (12 lines)
├── .env                             Credentials (gitignored)
├── pyproject.toml                   Dependencies
│
└── src/
    │
    ├── domain/                      ★ CORE BUSINESS LOGIC ★
    │   ├── models.py                Value objects & entities
    │   │   • Location, WeatherForecast, WeatherRecord
    │   │   • FootwearRecommendation (Enum: SHOE/SANDAL)
    │   │
    │   ├── repositories.py          Interfaces (ports)
    │   │   • WeatherProvider (protocol)
    │   │   • NotificationService (protocol)
    │   │   • WeatherRepository (protocol)
    │   │
    │   └── exceptions.py            Domain exceptions
    │
    ├── application/                 Business workflows
    │   ├── use_cases.py             Orchestration
    │   │   • SendWeatherReminderUseCase (main)
    │   │   • GetWeatherStatisticsUseCase
    │   │   • VerifySystemHealthUseCase
    │   │
    │   └── services.py              Business logic
    │       • RainBasedRecommendationService
    │       • MessageFormatter
    │
    ├── infrastructure/              External adapters
    │   ├── weather/
    │   │   └── open_meteo.py        HTTP → Open-Meteo API
    │   │
    │   ├── messaging/
    │   │   └── telegram.py          HTTP → Telegram Bot API
    │   │
    │   └── persistence/
    │       └── sqlite_repo.py       SQL → SQLite database
    │
    └── presentation/                Entry & config
        ├── config.py                Environment variables
        └── cli.py                   Dependency injection & logging
```
