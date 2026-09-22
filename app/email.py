"""Email delivery for authentication messages."""
import os
import smtplib
from email.message import EmailMessage


def send_otp_email(*, recipient: str, otp: str, expires_in_minutes: int) -> None:
    host = os.getenv("SMTP_HOST", "smtp.gmail.com")
    port = int(os.getenv("SMTP_PORT", "587"))
    username = os.getenv("SMTP_USERNAME")
    password = os.getenv("SMTP_PASSWORD")
    sender = os.getenv("SMTP_FROM_EMAIL") or username
    if not username or not password or not sender:
        raise RuntimeError("SMTP_USERNAME, SMTP_PASSWORD, and SMTP_FROM_EMAIL are required")

    message = EmailMessage()
    message["Subject"] = "Your Spend Tracker verification code"
    message["From"] = sender
    message["To"] = recipient
    message.set_content(
        f"Your Spend Tracker verification code is {otp}. It expires in "
        f"{expires_in_minutes} minutes."
    )

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        smtp.ehlo()
        smtp.starttls()
        smtp.ehlo()
        smtp.login(username, password)
        smtp.send_message(message)