import smtplib
import asyncio
from email.message import EmailMessage
from typing import Optional
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import partial
import time
from contextlib import contextmanager
from dataclasses import dataclass
from aiosmtplib import SMTP as AsyncSMTP
import threading

from src.app.config import settings

logger = logging.getLogger(__name__)

# Configuration class for email settings
@dataclass
class EmailConfig:
    THREAD_POOL_SIZE: int = 5
    MAX_RETRIES: int = 3
    RETRY_BASE_DELAY: float = 1.0
    RETRY_MAX_DELAY: float = 30.0
    CONNECTION_TIMEOUT: int = 10
    POOL_SIZE: int = 3
    MAX_EMAIL_SIZE: int = 25 * 1024 * 1024

# Initialize configuration from settings
email_config = EmailConfig(
    THREAD_POOL_SIZE=getattr(settings, "EMAIL_THREAD_POOL_SIZE", 5),
    MAX_RETRIES=getattr(settings, "EMAIL_MAX_RETRIES", 3),
    RETRY_BASE_DELAY=getattr(settings, "EMAIL_RETRY_BASE_DELAY", 1.0),
    RETRY_MAX_DELAY=getattr(settings, "EMAIL_RETRY_MAX_DELAY", 30.0),
    CONNECTION_TIMEOUT=getattr(settings, "SMTP_TIMEOUT", 10),
    POOL_SIZE=getattr(settings, "SMTP_POOL_SIZE", 3),
    MAX_EMAIL_SIZE=getattr(settings, "MAX_EMAIL_SIZE", 25 * 1024 * 1024),
)


# Connection pool for SMTP (synchronous)
class SMTPConnectionPool:
    def __init__(self):
        self._pool = []
        self._lock = threading.Lock()

    @contextmanager
    def get_connection(self):
        """Get a connection from the pool or create a new one."""
        with self._lock:
            if self._pool:
                conn = self._pool.pop()
            else:
                conn = smtplib.SMTP(
                    settings.SMTP_HOST,
                    settings.SMTP_PORT,
                    timeout=email_config.CONNECTION_TIMEOUT
                )
                conn.starttls()
                conn.login(settings.SMTP_USER, settings.SMTP_PASSWORD)

        try:
            yield conn
        finally:
            with self._lock:
                if len(self._pool) < email_config.POOL_SIZE:
                    self._pool.append(conn)
                else:
                    try:
                        conn.quit()
                    except Exception:
                        pass

# Create thread pool executor and connection pool
_email_executor = ThreadPoolExecutor(max_workers=email_config.THREAD_POOL_SIZE)
_smtp_pool = SMTPConnectionPool()

def _validate_message_size(msg: EmailMessage) -> None:
    msg_size = len(msg.as_bytes())
    if msg_size > email_config.MAX_EMAIL_SIZE:
        raise ValueError(f"Message too large ({msg_size} > {email_config.MAX_EMAIL_SIZE} bytes)")

def _create_email_message(
    subject: str,
    recipient: str,
    body: str,
    html: Optional[str] = None
) -> EmailMessage:
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = settings.EMAIL_FROM
    msg["To"] = recipient
    msg.set_content(body)
    if html:
        msg.add_alternative(html, subtype="html")
    _validate_message_size(msg)
    return msg

def _send_email_sync(
    subject: str,
    recipient: str,
    body: str,
    html: Optional[str] = None,
) -> None:
    """
    Synchronous email sending function to be run in a thread.
    Uses connection pooling for better performance.
    """
    try:
        msg = _create_email_message(subject, recipient, body, html)
        with _smtp_pool.get_connection() as server:
            server.send_message(msg)
        logger.info(f"Email sent successfully to {recipient}")
    except Exception as e:
        logger.error(f"Failed to send email to {recipient}: {e}")
        raise

def _send_email_sync_with_retry(
    subject: str,
    recipient: str,
    body: str,
    html: Optional[str] = None,
    retries: int = email_config.MAX_RETRIES,
    base_delay: float = email_config.RETRY_BASE_DELAY,
    max_delay: float = email_config.RETRY_MAX_DELAY,
) -> None:
    """
    Synchronous email sending with exponential backoff retry logic.
    """
    last_error = None
    for attempt in range(1, retries + 1):
        try:
            _send_email_sync(subject, recipient, body, html)
            return
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt}/{retries} failed for {recipient}: {e}")
            if attempt < retries:
                delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                logger.info(f"Retrying in {delay:.1f}s...")
                time.sleep(delay)
    logger.error(f"All {retries} attempts failed for {recipient}")
    raise last_error if last_error else Exception("Email sending failed")

async def send_email(
    subject: str,
    recipient: str,
    body: str,
    html: Optional[str] = None,
) -> None:
    """
    Async wrapper for sending emails using a thread pool.
    """
    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(
            _email_executor,
            partial(
                _send_email_sync_with_retry,
                subject=subject,
                recipient=recipient,
                body=body,
                html=html
            )
        )
    except Exception as e:
        logger.error(f"Email sending failed for {recipient}: {e}")
        raise

# Alternative async implementation using aiosmtplib with connection pooling
class AsyncSMTPConnectionPool:
    def __init__(self):
        self._pool = asyncio.Queue()
        self._lock = asyncio.Lock()

    async def get_connection(self):
        """Get or create an async SMTP connection."""
        if not self._pool.empty():
            return await self._pool.get()

        conn = AsyncSMTP(
            hostname=settings.SMTP_HOST,
            port=settings.SMTP_PORT,
            timeout=email_config.CONNECTION_TIMEOUT
        )
        await conn.connect()
        await conn.starttls()
        await conn.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        return conn

    async def release_connection(self, conn):
        """Release a connection back to the pool."""
        if self._pool.qsize() < email_config.POOL_SIZE:
            await self._pool.put(conn)
        else:
            await conn.quit()

_async_smtp_pool = AsyncSMTPConnectionPool()

async def send_email_async(
    subject: str,
    recipient: str,
    body: str,
    html: Optional[str] = None,
    retries: int = email_config.MAX_RETRIES,
    base_delay: float = email_config.RETRY_BASE_DELAY,
    max_delay: float = email_config.RETRY_MAX_DELAY,
) -> None:
    """
    Fully async email sending with connection pooling and retries.
    Alternative to the thread pool approach.
    """
    msg = _create_email_message(subject, recipient, body, html)
    last_error = None
    for attempt in range(1, retries + 1):
        conn = None
        try:
            conn = await _async_smtp_pool.get_connection()
            await conn.send_message(msg)
            logger.info(f"Email sent successfully to {recipient}")
            await _async_smtp_pool.release_connection(conn)
            return
        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt}/{retries} failed for {recipient}: {e}")
            if conn:
                try:
                    await conn.quit()
                except Exception:
                    pass
        if attempt < retries:
            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            logger.info(f"Retrying in {delay:.1f}s...")
            await asyncio.sleep(delay)
    logger.error(f"All {retries} attempts failed for {recipient}")
    raise last_error if last_error else Exception("Failed to send email")

async def send_verification_email(
    recipient_email: str,
    username: str,
    token: str,
    use_async_smtp: bool = False,
) -> None:
    """
    Compose and send an email verification message with a tokenized link.
    """
    verify_url = f"{settings.API_BASE_URL}/verify-email?token={token}"

    subject = "Please verify your email address"
    body = (
        f"Hi {username},\n\n"
        "Thanks for signing up! Please verify your email address by clicking the link below:\n\n"
        f"{verify_url}\n\n"
        "If you didn't sign up, please ignore this email.\n\n"
        "Best regards,\n"
        "The Team"
    )
    html = f"""
    <html>
      <body>
        <p>Hi {username},</p>
        <p>Thanks for signing up! Please verify your email address by clicking the link below:</p>
        <p><a href="{verify_url}">Verify Email Address</a></p>
        <p>If you didn't sign up, please ignore this email.</p>
        <p>Best regards,<br>The Team</p>
      </body>
    </html>
    """

    if use_async_smtp:
        await send_email_async(subject, recipient_email, body, html)
    else:
        await send_email(subject, recipient_email, body, html)

    logger.info(f"Verification email sent to {recipient_email}")
