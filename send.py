import os
from pathlib import Path

from dotenv import load_dotenv
from twilio.rest import Client


def get_required_environment_variable(variable_name):
    variable_value = os.getenv(variable_name, "").strip()
    if not variable_value:
        raise ValueError(f"Missing required environment variable: {variable_name}")
    return variable_value


def send_grocery_menu():
    load_dotenv(Path(__file__).resolve().parent / ".env")

    account_sid = get_required_environment_variable("TWILIO_ACCOUNT_SID")
    auth_token = get_required_environment_variable("TWILIO_AUTH_TOKEN")
    whatsapp_sender = get_required_environment_variable("TWILIO_WHATSAPP_FROM")
    whatsapp_recipient = get_required_environment_variable("TWILIO_WHATSAPP_TO")

    client = Client(account_sid, auth_token)
    message = client.messages.create(
        from_=whatsapp_sender,
        to=whatsapp_recipient,
        body=(
            "Grocery bot.\nReply with:\n"
            "add milk: Add an item\n"
            "remove milk: Remove an item\n"
            "3: Show list\n"
            "4: Clear list"
        ),
    )
    print(message.sid)


if __name__ == "__main__":
    send_grocery_menu()
