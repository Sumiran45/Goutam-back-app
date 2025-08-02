import aiosmtplib
from email.message import EmailMessage

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
EMAIL_SENDER = "anshu.aastha09@gmail.com"
EMAIL_PASSWORD = "wgrd edmc jrhg rbds"  # Use App Password if 2FA is on

async def send_verification_email(email: str, code: str):
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = email
    msg["Subject"] = "Verify your email"
    msg.set_content(f"Your verification code is: {code}")

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=EMAIL_SENDER,
        password=EMAIL_PASSWORD
    )

async def send_verification_success_email(email: str):
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = email
    msg["Subject"] = "Email Verified Successfully"
    msg.set_content(f"Congratulations! Your email has been successfully verified. You can now log in.")

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=EMAIL_SENDER,
        password=EMAIL_PASSWORD
    )

async def send_reset_password_email(email: str, reset_code: str):
    msg = EmailMessage()
    msg["From"] = EMAIL_SENDER
    msg["To"] = email
    msg["Subject"] = "Reset Your Password"
    msg.set_content(f"Your password reset code is: {reset_code}")

    await aiosmtplib.send(
        msg,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        start_tls=True,
        username=EMAIL_SENDER,
        password=EMAIL_PASSWORD
    )
