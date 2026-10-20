# Knowledge Tech Solutions

A responsive Flask portfolio and project-inquiry site. Demonstration portfolio cards are intentionally labelled and should be replaced with genuine project details before publication.

## Run locally (Windows PowerShell)

1. Open this folder in VS Code, then create and activate a virtual environment:
   ```powershell
   py -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
2. Install the dependencies and create your private configuration file:
   ```powershell
   pip install -r requirements.txt
   Copy-Item .env.example .env
   ```
3. Edit `.env`. Set a long random `SECRET_KEY`; set the sender and SMTP values. Keep this file private.
4. Run the site:
   ```powershell
   python app.py
   ```
   Open `http://127.0.0.1:5000`.

## SMTP setup and testing

The inquiry form sends only after the server validates it and SMTP accepts the message. Successful SMTP submission does not guarantee final inbox delivery. Use an authorized sender address for `MAIL_DEFAULT_SENDER`; recipients are sent to `BUSINESS_EMAIL`.

For Gmail, enable 2-Step Verification for the sender, create a Google App Password, and use it as `SMTP_PASSWORD`; use `smtp.gmail.com`, port `587`, and the sender’s address as `SMTP_USERNAME`. Never share or commit the app password.

Send a test inquiry from the contact section, then confirm that it arrives in the business mailbox (including spam). If delivery fails, verify the host, port, sender authorization, app password, and outbound SMTP rules. The visitor gets a safe error and alternative contact details rather than a false success message.

`STORE_INQUIRIES=true` maintains a local SQLite fallback at `instance/inquiries.sqlite`; it is excluded from Git. Limit access to the server account and delete records when no longer needed. There is intentionally no public endpoint for viewing inquiries.

## Tests

```powershell
pip install pytest
pytest
```

The tests mock SMTP: no real mail is sent. They cover pages, invalid submissions, accepted SMTP, and SMTP failure.

## Deployment

Use a Python host that supports environment variables and HTTPS. Set every `.env` value in the host’s dashboard, change `SESSION_COOKIE_SECURE=true`, and run Gunicorn with `gunicorn app:app` (or the host’s equivalent start command). Leave Flask debug mode disabled. Configure HTTPS before enabling secure cookies, point the custom-domain DNS record to the host as directed by that host, and verify both the domain and email delivery after deployment.

To update business details, edit the text in `templates/index.html` and the values in `.env`. To replace a demonstration project, update the `projects` list in the same template, add an approved visual to `static/images/`, and only publish verified technologies, status, and links.
