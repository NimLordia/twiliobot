from twilio.rest import Client
from .env import account_sid,auth_token

client = Client(account_sid, auth_token)

message = client.messages.create(
  from_='whatsapp:+14155238886',
  to='whatsapp:+972502528886',
  body= f'Grocey bot.\n reply the relevant number back:\n1: Add item\n2: Remove item\n3: Show list\n4: Clear list'
)

print(message.sid)