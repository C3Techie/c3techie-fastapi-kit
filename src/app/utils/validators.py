import phonenumbers
from phonenumbers.phonenumberutil import NumberParseException
import re
from typing import Optional
from email_validator import validate_email, EmailNotValidError
from app.utils.logging import get_logger
from app.core.password_policy import PasswordPolicy  # <-- Import centralized password policy

logger = get_logger(__name__)
PHONE_NUMBER_REGEX = r"^\+?[1-9]\d{1,14}$"
USERNAME_REGEX = r"^[a-zA-Z0-9_]+$"
STRONG_PASSWORD_REGEX = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*(),.?\":{}|<>])"


def validate_email_format(email: str) -> str:
    """Validates email format using comprehensive validation."""
    try:
        # Use email-validator for more robust validation
        validated_email = validate_email(email)
        return validated_email.email.lower()
    except EmailNotValidError:
        # Fallback to basic regex if email-validator fails
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            raise ValueError("Invalid email format")
        return email.lower()


def validate_name(name: str) -> str:
    """Validate first or last name.

    Rules:
    - Must be 2–50 characters
    - Must contain only letters, hyphens, and apostrophes
    - Capitalizes the first letter
    """
    if not name:
        raise ValueError("Name cannot be empty")

    if len(name) < 2 or len(name) > 50:
        raise ValueError("Name must be between 2 and 50 characters")

    if not re.match(r"^[a-zA-Z'-]+$", name):
        raise ValueError("Name may only contain letters, hyphens, and apostrophes")

    return name.capitalize()


def validate_phone_number(
    phone_number: str,
    country_code: Optional[str] = None,
    strict: bool = False
) -> str:
    """
    Validates and formats phone numbers using phonenumbers library with regex fallback.

    Args:
        phone_number: Input phone number (can contain formatting)
        country_code: Optional 2-letter ISO country code (e.g., 'US', 'GB')
        strict: If True, disables regex fallback and raises on parse errors

    Returns:
        E.164 formatted number (e.g., +14155552671)

    Raises:
        ValueError: For invalid numbers or parse failures
    """
    if not phone_number:
        raise ValueError("Phone number cannot be empty")

    # Sanitize input - keep only digits and leading +
    sanitized = re.sub(r"(?!^\+)[^\d]", "", phone_number)

    try:
        parsed = phonenumbers.parse(sanitized, country_code)
        if not phonenumbers.is_valid_number(parsed):
            raise ValueError("Invalid phone number for specified region")
        return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)

    except NumberParseException as e:
        if strict:
            raise ValueError("Invalid phone number format") from e

        logger.warning("Phone number validation fallback used for: %s", phone_number)
        if not re.match(PHONE_NUMBER_REGEX, sanitized):
            raise ValueError(
                "Phone number must be in international format (+[country code][number]) "
                "or valid local format with country code"
            )
        # Ensure E.164 format in fallback
        return sanitized if sanitized.startswith("+") else f"+{sanitized}"


def validate_optional_password(password: Optional[str]) -> Optional[str]:
    """Conditional password validation when field is optional."""
    return PasswordPolicy.validate(password) if password else None


def validate_username(username: str) -> str:
    """Ensures username contains only allowed characters and meets requirements."""
    if not username:
        raise ValueError("Username cannot be empty")

    if len(username) < 3:
        raise ValueError("Username must be at least 3 characters long")

    if len(username) > 50:
        raise ValueError("Username cannot exceed 50 characters")

    if not re.match(USERNAME_REGEX, username):
        raise ValueError("Username may only contain letters, numbers, and underscores")

    # Check for reserved usernames
    reserved_names = ['admin', 'root', 'user', 'test', 'api', 'www', 'mail', 'system']
    if username.lower() in reserved_names:
        raise ValueError("Username is reserved and cannot be used")

    return username


def validate_optional_username(username: Optional[str]) -> Optional[str]:
    """Conditional username validation when field is optional."""
    return validate_username(username) if username else None


def empty_string_to_none(value):
    """Converts empty string to None (for optional fields)."""
    if value == "":
        return None
    return value


def validate_role(role: str) -> str:
    """Validate that the role is either 'admin' or 'superadmin'."""
    allowed_roles = {"admin", "superadmin"}
    if role not in allowed_roles:
        raise ValueError("Role must be 'admin' or 'superadmin'")
    return role


def validate_permissions_list(permissions: Optional[list]) -> Optional[list]:
    """Validate that permissions is a list of strings."""
    if permissions is None:
        return permissions
    if not isinstance(permissions, list) or not all(isinstance(item, str) for item in permissions):
        raise ValueError("Permissions must be a list of strings")
    return permissions
