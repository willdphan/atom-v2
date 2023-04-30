from twilio.rest import Client
import config

twilio_client = Client(config.TWILIO_ACCOUNT_SID, config.TWILIO_AUTH_TOKEN)


def send_sms(sms_text, recipient_phone_number):
    print(f"Sending SMS to {recipient_phone_number} with content: {sms_text}")
    message = twilio_client.messages.create(
        body=sms_text,
        from_=config.TWILIO_PHONE_NUMBER,
        to=recipient_phone_number,
    )
    print(f"SMS sent to {recipient_phone_number}. Message SID: {message.sid}")
