import os
import logging
import aiosmtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# Azure Communication Services — only required in production (EMAIL_PROVIDER=acs)
# Install with: pip install azure-communication-email
try:
    from azure.communication.email import EmailClient
except ImportError:
    EmailClient = None

logger = logging.getLogger(__name__)

EMAIL_PROVIDER     = os.getenv("EMAIL_PROVIDER", "smtp")   # "acs" | "smtp"

# Azure Communication Services
ACS_CONNECTION_STR = os.getenv("ACS_CONNECTION_STRING", "")
ACS_SENDER         = os.getenv("ACS_SENDER_ADDRESS", "DoNotReply@yourdomain.azurecomm.net")

# SMTP (local dev)
SMTP_HOST          = os.getenv("SMTP_HOST", "sandbox.smtp.mailtrap.io")
SMTP_PORT          = int(os.getenv("SMTP_PORT", 587))
SMTP_USER          = os.getenv("SMTP_USER", "9f5760ceb954c9")
SMTP_PASSWORD      = os.getenv("SMTP_PASSWORD", "0b6abb77fba27c")
SMTP_FROM          = os.getenv("SMTP_FROM", "IQ_SPARK")


async def send_email(to: str, subject: str, html_body: str):
    """Route to ACS or SMTP based on EMAIL_PROVIDER env var."""
    if EMAIL_PROVIDER == "acs":
        await _send_via_acs(to, subject, html_body)
    else:
        await _send_via_smtp(to, subject, html_body)


async def _send_via_acs(to: str, subject: str, html_body: str):
    if not ACS_CONNECTION_STR:
        raise ValueError("ACS_CONNECTION_STRING is not set.")
    client  = EmailClient.from_connection_string(ACS_CONNECTION_STR)
    message = {
        "senderAddress": ACS_SENDER,
        "recipients":    {"to": [{"address": to}]},
        "content":       {"subject": subject, "html": html_body},
    }
    result = client.begin_send(message).result()
    logger.info(f"ACS email sent. ID: {result.get('id', 'N/A')}")


async def _send_via_smtp(to: str, subject: str, html_body: str):
    if not SMTP_USER or not SMTP_PASSWORD:
        raise ValueError("SMTP_USER and SMTP_PASSWORD must be set.")
    msg            = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"]    = SMTP_FROM
    msg["To"]      = to
    msg.attach(MIMEText(html_body, "html"))
    await aiosmtplib.send(
        msg, hostname=SMTP_HOST, port=SMTP_PORT,
        username=SMTP_USER, password=SMTP_PASSWORD, start_tls=True,
    )
    logger.info(f"SMTP email sent to {to}")
