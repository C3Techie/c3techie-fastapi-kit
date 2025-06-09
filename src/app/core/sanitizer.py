import html
import re
import phonenumbers


def sanitize_string(value: str) -> str:
    """Trim whitespace and escape HTML."""
    if not isinstance(value, str):
        return value
    return html.escape(value.strip())


def sanitize_email(email: str) -> str:
    """Trim and lowercase email."""
    if not isinstance(email, str):
        return email
    return email.strip().lower()


def sanitize_username(username: str) -> str:
    """Trim and remove unsafe characters from username (allow only letters, numbers, underscores)."""
    if not isinstance(username, str):
        return username
    username = username.strip()
    # Remove anything that's not a letter, number, or underscore
    return re.sub(r"[^\w]", "", username)


def sanitize_phone(
    phone: str,
    region: str = "US",
    fmt=phonenumbers.PhoneNumberFormat.E164
) -> str:
    """Normalize phone number to the specified format (default E.164)."""
    try:
        parsed = phonenumbers.parse(phone, region)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, fmt)
    except Exception:
        pass
    return phone.strip()
