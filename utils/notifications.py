import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import logging
from typing import Optional

logger = logging.getLogger(__name__)


async def send_appointment_confirmation(
        patient_email: str,
        doctor_name: str,
        appointment_date: datetime
):
    """Send appointment confirmation email"""
    try:
        # Email configuration (replace with your SMTP settings)
        smtp_server = "smtp.gmail.com"
        smtp_port = 587
        sender_email = "your-email@gmail.com"
        sender_password = "your-app-password"

        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = patient_email
        message["Subject"] = "Appointment Confirmation"

        body = f"""
        Dear Patient,

        Your appointment has been confirmed with {doctor_name}.

        Appointment Details:
        - Doctor: {doctor_name}
        - Date & Time: {appointment_date.strftime("%B %d, %Y at %I:%M %p")}

        Please arrive 15 minutes early for your appointment.

        Best regards,
        Medical Center Team
        """

        message.attach(MIMEText(body, "plain"))

        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            text = message.as_string()
            server.sendmail(sender_email, patient_email, text)

        logger.info(f"Appointment confirmation sent to {patient_email}")

    except Exception as e:
        logger.error(f"Failed to send appointment confirmation: {e}")
