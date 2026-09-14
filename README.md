# WhatsApp Grocery List Bot

A Python bot for managing a shared grocery list through WhatsApp. Send a message to add or remove an item, view the list, or clear it. SQLite keeps the list between application restarts.

Built as a learning project to practice Flask webhooks, SQLAlchemy database operations, and integration with the Twilio WhatsApp API.

## Commands

| Message | Action |
| --- | --- |
| `add milk` | Add milk to the list |
| `remove milk` | Remove milk from the list |
| `3` | Show the list |
| `4` | Clear the list |

Send `help` to see the menu. Item names are converted to lowercase. Everyone messaging the bot uses the same list.

## How it works

1. A user sends a WhatsApp message to the configured Twilio number.
2. Twilio forwards the message to the Flask application's `POST /webhook` endpoint.
3. The application verifies Twilio's signature before reading the command or accessing SQLite through SQLAlchemy.
4. The webhook returns a TwiML response that Twilio delivers back to WhatsApp.

`send.py` is a separate, optional script that sends the command menu through Twilio's REST API.

## Local setup

You will need Python, Git, and a Twilio account with access to the WhatsApp Sandbox. The WhatsApp demo also needs a phone running WhatsApp and an HTTPS tunnel to the local server. Dependency versions are listed in `requirements.txt`.

### 1. Install dependencies

These commands use Windows PowerShell. Run all application commands from the repository directory so SQLite uses the same local database.

```powershell
git clone https://github.com/NimLordia/twiliobot.git
cd twiliobot
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

If the repository is already cloned, start from its directory and skip the first two commands. If `py` is unavailable, use `python` if it points to your Python installation. Using the virtual environment's Python directly avoids needing to activate it.

On macOS or Linux, create the environment with `python3 -m venv .venv` and use `.venv/bin/python` in place of `.\.venv\Scripts\python.exe` below.

### 2. Configure the webhook

Copy the configuration template in PowerShell:

```powershell
Copy-Item .env.example .env
```

On macOS or Linux, use `cp .env.example .env`. If you already have a `.env` file, edit it instead of overwriting it.

Set `TWILIO_AUTH_TOKEN` to your account's primary auth token from the Twilio Console. Start an HTTPS tunnel forwarding to `http://127.0.0.1:5000`, then set `TWILIO_WEBHOOK_URL` to its full public URL including `/webhook`, for example `https://your-tunnel-host/webhook`. Keep the tunnel running for the next steps; it will reach the app once the server starts.

Use exactly the same URL in `.env` and in the Twilio Console, including any query string. Signature verification uses this public URL even when the tunnel forwards to local HTTP. Keep `.env` private; it is ignored by Git. Existing environment variables take precedence over `.env` values.

The receiver requires these two settings. Missing settings or an invalid webhook URL return HTTP `503`; unsigned requests and invalid signatures return HTTP `403` before any list operations. Verification stays enabled during testing and debugging. See Twilio's [request security documentation](https://www.twilio.com/docs/usage/security).

### 3. Start the webhook

```powershell
.\.venv\Scripts\python.exe -m flask --app receive --no-debug run --host 127.0.0.1 --port 5000
```

The webhook accepts form-encoded `POST` requests at `http://127.0.0.1:5000/webhook`. There is no browser interface. `grocery_list.db` and its tables are created automatically when the application starts; the database is ignored by Git.

This command starts the app with debug mode disabled. Running `receive.py` directly also disables debug mode and listens only on `127.0.0.1`. Both launch a development server; see the [Flask development server documentation](https://flask.palletsprojects.com/en/stable/server/) for deployment limitations.

After configuring the receiver, check that an unsigned request is rejected from another PowerShell window:

```powershell
Invoke-RestMethod -Uri http://127.0.0.1:5000/webhook -Method Post -Body @{ Body = "3" }
```

PowerShell should report HTTP `403 Forbidden`. This is expected: local requests also need a valid Twilio signature. The automated tests below exercise accepted requests using dummy credentials.

### 4. Connect WhatsApp through Twilio

1. Open the WhatsApp Sandbox in your Twilio Console.
2. From your phone, send the displayed `join <sandbox code>` message to the displayed Sandbox number.
3. Confirm the HTTPS tunnel from step 2 is still forwarding to `http://127.0.0.1:5000`.
4. Set the Sandbox's incoming-message webhook URL to the exact `TWILIO_WEBHOOK_URL` value, select `POST`, and save.
5. Send `add milk`, then `3`, to the Sandbox number to try the bot.

Keep the Flask server and tunnel running during the demo. If the tunnel URL changes, update both `.env` and the Twilio webhook setting, then restart Flask. Follow Twilio's [Sandbox setup guide](https://www.twilio.com/docs/whatsapp/sandbox) for the current Console instructions.

### 5. Send the menu (optional)

To send the menu, fill in these additional settings in the existing `.env` file. `send.py` also uses the `TWILIO_AUTH_TOKEN` set in step 2:

| Setting | Value |
| --- | --- |
| `TWILIO_ACCOUNT_SID` | Your account SID from the Twilio Console |
| `TWILIO_WHATSAPP_FROM` | The Sandbox sender, formatted as `whatsapp:+<country code><number>` |
| `TWILIO_WHATSAPP_TO` | Your joined recipient, in the same format |

Use the full international phone numbers without spaces or angle brackets. These additional settings are used by `send.py`.

Send a WhatsApp message from the recipient phone to the Sandbox before running the script. The menu is a free-form message, so it requires an active 24-hour customer service window. See Twilio's [messaging window documentation](https://www.twilio.com/docs/whatsapp/api).

```powershell
.\.venv\Scripts\python.exe send.py
```

This sends one real WhatsApp message and prints its Twilio message SID. It stops before sending if a required setting is missing or blank. A returned SID identifies the API request's message; it does not guarantee delivery to the phone.

## Automated checks

After installing the dependencies, run:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

The tests use dummy credentials, Flask's test client, and Twilio's real signature validator. Database functions are replaced during these tests, so they do not change your grocery list or send WhatsApp messages. They cover accepted and rejected signatures, changed message bodies, tunnel URLs, missing input, command handling, XML responses, and safe startup defaults.

## Main files

| File | Purpose |
| --- | --- |
| `receive.py` | Flask webhook and command handling |
| `database.py` | SQLite model and grocery-list operations |
| `send.py` | Optional outbound menu message |
| `.env.example` | Configuration template with no credentials |
| `.gitignore` | Excludes private settings and generated local files |
| `requirements.txt` | Direct Python dependencies |
| `tests/test_receive.py` | Webhook security and command tests |

## Current limitations

- The list is shared across all senders; there are no separate user accounts or lists.
- Any sender who can message the configured Twilio number can change the shared list; signature verification authenticates Twilio, not membership in a household.
- This is a development demo. Production deployment needs a production server configuration.

Next improvements: separate lists or sender permissions, and database integration tests.
