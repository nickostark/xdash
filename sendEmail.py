import os
from email.message import EmailMessage
import ssl
import smtplib


def _required_env(name):
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def send_email(subject, body, to_email):
    smtp_username = _required_env("SMTP_USERNAME")
    smtp_password = _required_env("SMTP_PASSWORD")
    sender_email = _required_env("SMTP_SENDER_EMAIL")  # e.g., notifications@example.com
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "465"))

    em = EmailMessage()
    em["From"] = sender_email
    em["To"] = to_email
    em["Subject"] = subject
    em.set_content(body)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(smtp_server, smtp_port, context=context) as smtp:
        smtp.login(smtp_username, smtp_password)
        smtp.sendmail(sender_email, to_email, em.as_string())
