import os
from flask import Flask, request
from twilio.twiml.messaging_response import MessagingResponse
from databse import add_item, remove_item, get_list, clear_list

app = Flask(__name__)

@app.route("/webhook", methods=["POST"])
def webhook():
    """Handles incoming WhatsApp messages from Twilio."""
    incoming_msg = request.form.get("Body").strip().lower()
    sender = request.form.get("From")

    # Twilio response object
    response = MessagingResponse()
    
    if incoming_msg == "1":
        reply = "You chose: *Add item*. Send the item name."
    elif incoming_msg.startswith("add "):
        item = incoming_msg[4:]
        add_item(item)
        reply = f"✅ *{item}* added to the grocery list!"
    elif incoming_msg == "2":
        reply = "You chose: *Remove item*. Send the item name."
    elif incoming_msg.startswith("remove "):
        item = incoming_msg[7:]
        remove_item(item)
        reply = f"❌ *{item}* removed from the grocery list!"
    elif incoming_msg == "3":
        items = get_list()
        if items:
            reply = "🛒 *Your Grocery List:*\n" + "\n".join(f"- {item}" for item in items)
        else:
            reply = "📭 Your grocery list is empty."
    elif incoming_msg == "4":
        clear_list()
        reply = "🧹 Grocery list cleared!"
    else:
        reply = (
            "🤖 *Grocery Bot*\n"
            "Reply with a number:\n"
            "1️⃣ Add item\n"
            "2️⃣ Remove item\n"
            "3️⃣ Show list\n"
            "4️⃣ Clear list"
        )

    response.message(reply)
    return str(response)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
