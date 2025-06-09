import re

class PasswordPolicy:
    """
    Enforces strong password requirements:
      - Minimum 8 characters
      - At least one uppercase letter
      - At least one lowercase letter
      - At least one digit
      - At least one special character
      - Not a common weak password
    """

    @staticmethod
    def validate(password: str) -> str:
        if not password:
            raise ValueError("Password cannot be empty")
        if len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        if len(password) > 128:
            raise ValueError("Password cannot exceed 128 characters")
        if not any(c.isupper() for c in password):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in password):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in password):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise ValueError("Password must contain at least one special character")
        if password.lower() in ['password', '12345678', 'qwerty123']:
            raise ValueError("Password is too common and easily guessable")
        return password
