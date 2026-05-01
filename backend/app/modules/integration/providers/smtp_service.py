"""Generic SMTP email integration service."""

import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any

from app.modules.integration.providers.base import BaseProviderService


class SMTPService(BaseProviderService):
    """Generic SMTP email provider service."""

    def __init__(self, credentials: dict, config: dict | None = None):
        """Initialize SMTP service.

        Expected credentials:
            host: str (SMTP server hostname)
            port: int (SMTP port, usually 587 for TLS)
            username: str
            password: str
            use_tls: bool
            from_email: str
        """
        super().__init__(credentials, config)

        self.host = credentials["host"]
        self.port = credentials["port"]
        self.username = credentials["username"]
        self.password = credentials["password"]
        self.use_tls = credentials.get("use_tls", True)
        self.from_email = credentials["from_email"]

    async def test_connection(self) -> dict[str, Any]:
        """Test SMTP connection and authentication.

        Returns:
            Dict with test results
        """
        try:
            # Try to connect and authenticate
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.host, self.port)

            server.login(self.username, self.password)
            server.quit()

            return {
                "success": True,
                "message": f"Successfully connected to SMTP server {self.host}:{self.port}",
            }

        except smtplib.SMTPAuthenticationError as e:
            return {
                "success": False,
                "message": f"SMTP authentication failed: {str(e)}",
            }
        except Exception as e:
            return {
                "success": False,
                "message": f"SMTP connection failed: {str(e)}",
            }

    async def send_email(
        self,
        recipient: str,
        subject: str,
        body_html: str | None = None,
        body_text: str | None = None,
    ) -> dict[str, Any]:
        """Send email via SMTP.

        Args:
            recipient: Recipient email address
            subject: Email subject
            body_html: HTML body (optional)
            body_text: Plain text body (optional)

        Returns:
            Dict with send results

        Raises:
            Exception: If email send fails
        """
        try:
            # Create message
            msg = MIMEMultipart("alternative")
            msg["From"] = self.from_email
            msg["To"] = recipient
            msg["Subject"] = subject

            # Add text body
            if body_text:
                text_part = MIMEText(body_text, "plain")
                msg.attach(text_part)

            # Add HTML body
            if body_html:
                html_part = MIMEText(body_html, "html")
                msg.attach(html_part)

            # Send email
            if self.use_tls:
                server = smtplib.SMTP(self.host, self.port)
                server.starttls()
            else:
                server = smtplib.SMTP(self.host, self.port)

            server.login(self.username, self.password)
            server.sendmail(self.from_email, [recipient], msg.as_string())
            server.quit()

            return {
                "success": True,
                "message": f"Email sent to {recipient}",
                "recipient": recipient,
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to send email: {str(e)}",
                "error": str(e),
            }
