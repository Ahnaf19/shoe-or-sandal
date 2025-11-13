"""
Telegram notification service implementation.

Concrete implementation of NotificationService using Telegram Bot API.
"""

import logging
import time
from typing import Optional
import requests

from src.domain.repositories import NotificationService
from src.domain.exceptions import NotificationException, ExternalServiceException
from src.domain.utils import mask_sensitive_data

logger = logging.getLogger(__name__)


class TelegramNotificationService(NotificationService):
    """
    Notification service using Telegram Bot API.

    Implements the NotificationService interface with Telegram-specific logic.
    Uses simple HTTP requests - no complex library dependencies.
    """

    API_BASE_URL = "https://api.telegram.org"
    TIMEOUT_SECONDS = 10
    MAX_RETRIES = 3

    def __init__(
        self,
        bot_token: str,
        chat_id: str,
        timeout: int = TIMEOUT_SECONDS,
        max_retries: int = MAX_RETRIES,
    ) -> None:
        """
        Initialize Telegram service.

        Args:
            bot_token: Telegram bot token from BotFather
            chat_id: Telegram chat ID to send messages to
            timeout: Request timeout in seconds
            max_retries: Maximum number of retry attempts

        Raises:
            ValueError: If bot_token or chat_id is empty
        """
        if not bot_token:
            raise ValueError("bot_token cannot be empty")
        if not chat_id:
            raise ValueError("chat_id cannot be empty")

        self._bot_token = bot_token
        self._chat_id = chat_id
        self._timeout = timeout
        self._max_retries = max_retries
        self._api_url = f"{self.API_BASE_URL}/bot{bot_token}"

        masked_chat_id = mask_sensitive_data(chat_id, visible_chars=4)
        logger.info(
            f"Initialized TelegramNotificationService "
            f"(chat_id={masked_chat_id}, timeout={timeout}s)"
        )

    def send_message(self, message: str, parse_mode: str = "Markdown") -> bool:
        """
        Send a message via Telegram Bot API.

        Implements retry logic with exponential backoff for resilience.

        Args:
            message: Message text to send
            parse_mode: Message formatting ('Markdown' or 'HTML')

        Returns:
            True if sent successfully, False otherwise

        Raises:
            NotificationException: If unable to send after all retries
        """
        if not message or not message.strip():
            logger.warning("Attempted to send empty message")
            return False

        masked_chat_id = mask_sensitive_data(self._chat_id, visible_chars=4)
        logger.info(f"Sending message to chat {masked_chat_id} (length: {len(message)})")

        url = f"{self._api_url}/sendMessage"
        payload = {
            "chat_id": self._chat_id,
            "text": message,
            "parse_mode": parse_mode,
        }

        last_exception: Optional[Exception] = None

        for attempt in range(1, self._max_retries + 1):
            try:
                logger.debug(f"Send attempt {attempt}/{self._max_retries}")

                response = requests.post(
                    url,
                    json=payload,
                    timeout=self._timeout,
                )
                response.raise_for_status()

                result = response.json()

                if result.get("ok"):
                    message_id = result.get("result", {}).get("message_id")
                    logger.info(f"Message sent successfully (message_id={message_id})")
                    return True
                else:
                    error_desc = result.get("description", "Unknown error")
                    logger.error(f"Telegram API returned error: {error_desc}")
                    last_exception = NotificationException(
                        f"Telegram API error: {error_desc}"
                    )

            except requests.Timeout as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} timed out: {e}")

            except requests.RequestException as e:
                last_exception = e
                logger.warning(f"Attempt {attempt} failed: {e}")

            except Exception as e:
                last_exception = e
                logger.error(f"Unexpected error on attempt {attempt}: {e}", exc_info=True)

            # Retry with exponential backoff
            if attempt < self._max_retries:
                wait_time = 2 ** (attempt - 1)
                logger.info(f"Retrying in {wait_time}s...")
                time.sleep(wait_time)

        # All retries failed
        error_msg = f"Failed to send message after {self._max_retries} attempts"
        logger.error(error_msg)
        raise NotificationException(error_msg) from last_exception

    def test_connection(self) -> bool:
        """
        Test Telegram bot connection by getting bot information.

        Returns:
            True if bot is properly configured and accessible

        Raises:
            ExternalServiceException: If unable to connect
        """
        logger.info("Testing Telegram bot connection...")

        url = f"{self._api_url}/getMe"

        try:
            response = requests.get(url, timeout=self._timeout)
            response.raise_for_status()

            result = response.json()

            if result.get("ok"):
                bot_info = result.get("result", {})
                bot_name = bot_info.get("first_name", "Unknown")
                bot_username = bot_info.get("username", "Unknown")

                logger.info(f"Bot connected: {bot_name} (@{bot_username})")
                return True
            else:
                error_desc = result.get("description", "Unknown error")
                logger.error(f"Bot connection failed: {error_desc}")
                raise ExternalServiceException(
                    "Telegram API",
                    f"Bot connection failed: {error_desc}",
                )

        except requests.RequestException as e:
            error_msg = f"Failed to connect to Telegram API: {str(e)}"
            logger.error(error_msg)
            raise ExternalServiceException("Telegram API", error_msg) from e


class ConsolNotificationService(NotificationService):
    """
    Console notification service for testing/development.

    Prints messages to console instead of sending to external service.
    Useful for local development and testing.
    """

    def __init__(self) -> None:
        """Initialize console notification service."""
        logger.info("Initialized ConsoleNotificationService")

    def send_message(self, message: str) -> bool:
        """
        Print message to console.

        Args:
            message: Message to print

        Returns:
            Always returns True
        """
        print("\n" + "=" * 50)
        print("NOTIFICATION MESSAGE")
        print("=" * 50)
        print(message)
        print("=" * 50 + "\n")
        logger.info("Message printed to console")
        return True

    def test_connection(self) -> bool:
        """
        Test console connection (always succeeds).

        Returns:
            Always returns True
        """
        logger.info("Console notification service is ready")
        return True
