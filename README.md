\# WhatsApp Grocery List Bot



A simple WhatsApp bot for managing a shared grocery list.



This project was created as a learning project using Python, Flask, Twilio, SQLAlchemy, and SQLite.



\## Features



Users can manage their grocery list by sending WhatsApp messages:



\* `add milk` — Add an item

\* `remove milk` — Remove an item

\* `3` — Display the current grocery list

\* `4` — Clear the grocery list



The grocery list is stored locally in an SQLite database.



\## Technologies



\* Python

\* Flask

\* Twilio WhatsApp API

\* SQLAlchemy

\* SQLite



\## Installation



Clone the repository and enter the project directory:



```bash

git clone https://github.com/NimLordia/twiliobot.git

cd twiliobot

```



Create and activate a virtual environment:



```bash

python -m venv .venv

```



On Windows:



```bash

.venv\\Scripts\\activate

```



Install the dependencies:



```bash

pip install -r requirements.txt

```



\## Running the Webhook



Start the Flask application:



```bash

python receive.py

```



The webhook will run locally at:



```text

http://localhost:5000/webhook

```



To receive Twilio webhook requests during local development, expose port `5000` using a tunnelling service and configure the Twilio WhatsApp webhook to use:



```text

https://your-public-url/webhook

```



\## Project Structure



```text

twiliobot/

├── database.py          # Database model and grocery-list operations

├── receive.py           # Flask webhook for incoming WhatsApp messages

├── send.py              # Sends the initial WhatsApp message

├── grocery\_list.db      # SQLite database

└── requirements.txt     # Python dependencies

```



\## Notes



This is an educational project and is not intended for production use.



