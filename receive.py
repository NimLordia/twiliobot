import os
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import load_dotenv
from flask import Flask, Response, abort, request
from twilio.request_validator import RequestValidator
from twilio.twiml.messaging_response import MessagingResponse

from database import add_item, remove_item, get_list, clear_list

load_dotenv(Path(__file__).resolve().parent / ".env")

app = Flask(__name__)
app.config["TWILIO_AUTH_TOKEN"] = os.getenv("TWILIO_AUTH_TOKEN", "").strip()
app.config["TWILIO_WEBHOOK_URL"] = os.getenv("TWILIO_WEBHOOK_URL", "").strip()


def validate_twilio_request():
    """Reject requests that are not signed for the configured public webhook."""
    auth_token = app.config["TWILIO_AUTH_TOKEN"]
    webhook_url = app.config["TWILIO_WEBHOOK_URL"]
    if not auth_token or not webhook_url:
        abort(503, description="Set TWILIO_AUTH_TOKEN and TWILIO_WEBHOOK_URL.")

    try:
        webhook_url_parts = urlsplit(webhook_url)
        webhook_port = webhook_url_parts.port
    except ValueError:
        abort(503, description="TWILIO_WEBHOOK_URL is invalid.")

    if (
        webhook_url_parts.scheme != "https"
        or not webhook_url_parts.hostname
        or webhook_url_parts.path != "/webhook"
        or webhook_url_parts.username is not None
        or webhook_url_parts.password is not None
        or webhook_url_parts.fragment
        or webhook_port == 0
        or any(character.isspace() for character in webhook_url)
    ):
        abort(503, description="TWILIO_WEBHOOK_URL must be an HTTPS /webhook URL.")

    # The tunnel's local HTTP URL differs from the public URL Twilio signs.
    if request.query_string != webhook_url_parts.query.encode("utf-8"):
        abort(403)

    request_signature = request.headers.get("X-Twilio-Signature", "")
    request_validator = RequestValidator(auth_token)
    if not request_validator.validate(webhook_url, request.form, request_signature):
        abort(403)


@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles incoming WhatsApp messages."""
    validate_twilio_request()
    incoming_message = request.form.get("Body", "").strip().lower()
    messaging_response = MessagingResponse()

    if incoming_message.startswith("add "):
        grocery_item_name = incoming_message[4:].strip()
        add_item(grocery_item_name)
        reply_message = f"✅ *{grocery_item_name}* added to the grocery list!"
    elif incoming_message.startswith("remove "):
        grocery_item_name = incoming_message[7:].strip()
        remove_item(grocery_item_name)
        reply_message = f"❌ *{grocery_item_name}* removed from the grocery list!"
    elif incoming_message == "3":
        grocery_items = get_list()
        if grocery_items:
            reply_message = "🛒 *Your Grocery List:*\n" + "\n".join(
                f"- {grocery_item}" for grocery_item in grocery_items
            )
        else:
            reply_message = "📭 Your grocery list is empty."
    elif incoming_message == "4":
        clear_list()
        reply_message = "🧹 Grocery list cleared!"
    else:
        reply_message = (
            "🤖 *Grocery Bot*\n"
            "Reply with:\n"
            "add milk: Add an item\n"
            "remove milk: Remove an item\n"
            "3️⃣ Show list\n"
            "4️⃣ Clear list"
        )

    messaging_response.message(reply_message)
    return Response(str(messaging_response), mimetype="application/xml")


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=False)
