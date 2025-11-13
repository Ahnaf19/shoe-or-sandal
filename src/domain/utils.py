"""
Domain utilities.

Helper functions for the domain layer.
"""


def mask_sensitive_data(value: str, visible_chars: int = 4, mask_char: str = "*") -> str:
    """
    Mask sensitive data for safe logging.

    Shows only the last N characters, masks the rest.

    Args:
        value: The sensitive string to mask
        visible_chars: Number of characters to show at the end
        mask_char: Character to use for masking

    Returns:
        Masked string (e.g., "****5443" for chat ID)

    Examples:
        >>> mask_sensitive_data("1234567890")
        '******7890'
        >>> mask_sensitive_data("1234567890", visible_chars=3)
        '*******890'
    """
    if not value:
        return ""

    if len(value) <= visible_chars:
        # If value is too short, just show it (or mask completely)
        return value

    mask_length = len(value) - visible_chars
    return mask_char * mask_length + value[-visible_chars:]
