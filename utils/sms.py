# utils/sms.py
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
import os
from dotenv import load_dotenv
import logging

load_dotenv()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_SID, TWILIO_AUTH_TOKEN)


async def send_verification_sms(phone_number: str, code: str):
    try:
        message = client.messages.create(
            body=f"Your verification code is: {code}",
            from_=TWILIO_PHONE_NUMBER,
            to=phone_number
        )
        logging.info(f"SMS sent successfully to {phone_number}, SID: {message.sid}")
        return {"success": True, "sid": message.sid}

    except TwilioRestException as e:
        logging.error(f"Twilio Error: {e}")

        # Check if it's a permissions/verification issue
        if "Permission to send an SMS has not been enabled" in str(e):
            logging.warning(f"Phone number {phone_number} not verified in Twilio trial account")
            # For development, you might want to return success to continue testing
            # In production, you'd return the actual error
            return {"success": False, "error": "Phone number not verified in trial account"}

        # Other Twilio errors
        return {"success": False, "error": str(e)}

    except Exception as e:
        logging.error(f"Unexpected error sending SMS: {e}")
        return {"success": False, "error": "Failed to send SMS"}

def send_otp(phone: str):
    verification = client.verify.v2.services(VERIFY_SID).verifications.create(
        to=phone,
        channel="sms"
    )
    return verification.status

def verify_otp(phone: str, code: str) -> bool:
    check = client.verify.v2.services(VERIFY_SID).verification_checks.create(
        to=phone,
        code=code
    )
    return check.status == "approved"
