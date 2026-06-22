import os
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")

def send_whatsapp_confirmation(to: str, patient: str, doctor: str, time: str):
    """
    Sends a WhatsApp appointment confirmation message via Twilio.
    """
    if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
        print("WARNING: Twilio credentials not configured. Skipping WhatsApp confirmation.")
        return None

    # Ensure correct format for WhatsApp numbers
    to_formatted = to if to.startswith("whatsapp:") else f"whatsapp:{to}"
    from_formatted = TWILIO_WHATSAPP_FROM if TWILIO_WHATSAPP_FROM.startswith("whatsapp:") else f"whatsapp:{TWILIO_WHATSAPP_FROM}"

    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    
    body = (
        f"Hi {patient}! Your appointment with {doctor} is confirmed for {time}. \n"
        f"- CliniCall"
    )
    
    try:
        message = client.messages.create(
            body=body,
            from_=from_formatted,
            to=to_formatted
        )
        print(f"WhatsApp confirmation sent successfully. SID: {message.sid}")
        return message.sid
    except Exception as e:
        print(f"Failed to send WhatsApp confirmation via Twilio: {e}")
        return None
