"""Unit tests for domain utilities."""

import pytest

from src.domain.utils import mask_sensitive_data


class TestMaskSensitiveData:
    """Tests for mask_sensitive_data function."""

    def test_mask_with_default_params(self):
        """Test masking with default parameters (4 visible chars)."""
        result = mask_sensitive_data("1234567890")
        assert result == "******7890"
        assert len(result) == 10

    def test_mask_with_custom_visible_chars(self):
        """Test masking with custom number of visible characters."""
        result = mask_sensitive_data("1234567890", visible_chars=3)
        assert result == "*******890"

    def test_mask_with_custom_mask_char(self):
        """Test masking with custom mask character."""
        result = mask_sensitive_data("1234567890", mask_char="#")
        assert result == "######7890"

    def test_mask_short_string(self):
        """Test that short strings are returned as-is."""
        result = mask_sensitive_data("123", visible_chars=4)
        assert result == "123"

    def test_mask_exact_length_string(self):
        """Test string exactly matching visible_chars length."""
        result = mask_sensitive_data("1234", visible_chars=4)
        assert result == "1234"

    def test_mask_empty_string(self):
        """Test empty string returns empty."""
        result = mask_sensitive_data("")
        assert result == ""

    def test_mask_chat_id(self):
        """Test masking a typical Telegram chat ID."""
        chat_id = "8372775443"
        result = mask_sensitive_data(chat_id, visible_chars=4)
        assert result == "******5443"
        assert len(result) == len(chat_id)

    def test_mask_bot_token(self):
        """Test masking a typical bot token (show last 8 chars)."""
        token = "123456789:ABCdefGHIjklMNOpqrsTUVwxyz"
        result = mask_sensitive_data(token, visible_chars=8)
        assert result.endswith("sTUVwxyz")
        assert result.startswith("*")

    def test_mask_preserves_length(self):
        """Test that masking preserves original string length."""
        values = ["abc123", "1234567890", "short", "verylongstring"]
        for value in values:
            result = mask_sensitive_data(value, visible_chars=3)
            assert len(result) == len(value)
