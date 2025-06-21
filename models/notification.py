# utils/notification.py

from twilio.rest import Client
import os

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)


def send_sms(to: str, message: str):
    """
    Sends an SMS using Twilio
    """
    try:
        sms = client.messages.create(
            body=message,
            from_=TWILIO_PHONE_NUMBER,
            to=to
        )
        print(f"SMS sent: SID {sms.sid}")
    except Exception as e:
        print(f"Failed to send SMS: {e}")


def send_whatsapp(to: str, message: str):
    """
    Sends a WhatsApp message using Twilio Sandbox (for testing)
    Make sure you’ve joined Twilio Sandbox and used the right `to` format: 'whatsapp:+91xxxxxxxxxx'
    """
    try:
        whatsapp_msg = client.messages.create(
            body=message,
            from_='whatsapp:+14155238886',  # Twilio WhatsApp sandbox number
            to=f"whatsapp:{to}"              # Format: whatsapp:+91xxxxxxxxxx
        )
        print(f"WhatsApp message sent: SID {whatsapp_msg.sid}")
    except Exception as e:
        print(f"Failed to send WhatsApp message: {e}")
