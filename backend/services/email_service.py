import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

try:
    from config import settings
except ModuleNotFoundError:
    from backend.config import settings

logger = logging.getLogger(__name__)


def send_password_reset_email(to_email: str, reset_token: str) -> bool:
    """
    Sends a password reset email containing a reset link.
    IMPORTANT: Never log reset_token or passwords.
    If SMTP credentials are not configured, logs a safe notice without revealing secrets.
    """
    reset_url = f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"

    if not settings.SMTP_HOST or not settings.SMTP_USER:
        # SMTP is not configured in this environment.
        # Log a generic message without exposing sensitive token values.
        logger.info(
            "Password reset email requested for %s. (SMTP not configured; simulated dispatch).",
            to_email,
        )
        return False

    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = "SubscriptIQ Password Reset Request"
        msg["From"] = settings.EMAILS_FROM_EMAIL
        msg["To"] = to_email

        text_content = (
            f"Hello,\n\n"
            f"You requested to reset your SubscriptIQ password.\n"
            f"Click or open the link below to set a new password:\n{reset_url}\n\n"
            f"This link expires in {settings.RESET_TOKEN_EXPIRE_MINUTES} minutes and is single-use.\n"
            f"If you did not make this request, you can safely ignore this email.\n"
        )

        html_content = f"""
        <html>
          <body>
            <h3>SubscriptIQ Password Reset</h3>
            <p>You requested to reset your password.</p>
            <p><a href="{reset_url}" style="padding:10px 16px;background:#4f46e5;color:#ffffff;text-decoration:none;border-radius:6px;">Reset Password</a></p>
            <p>Or paste this URL in your browser: <br/>{reset_url}</p>
            <p><em>This link is single-use and will expire in {settings.RESET_TOKEN_EXPIRE_MINUTES} minutes.</em></p>
          </body>
        </html>
        """

        msg.attach(MIMEText(text_content, "plain"))
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10) as server:
            server.starttls()
            if settings.SMTP_PASSWORD:
                server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.send_message(msg)

        logger.info("Password reset email sent to recipient.")
        return True
    except Exception as exc:
        # Log error type without exposing credentials or tokens
        logger.error("Failed to send password reset email: %s", type(exc).__name__)
        return False
