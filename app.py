
import html
import logging
import os
import smtplib
import sqlite3
from datetime import datetime, timezone
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, url_for
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import BooleanField, SelectField, StringField, TextAreaField
from wtforms.validators import (
    DataRequired,
    Length,
    Optional,
    ValidationError,
)

# --------------------------------------------------
# Configuration
# --------------------------------------------------

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

PROJECT_TYPES = [
    ("", "Choose a project type"),
    ("website", "Website development"),
    ("software", "Custom software"),
    ("ai", "AI or machine learning"),
    ("business", "Business management system"),
    ("analytics", "Data analytics"),
    ("api", "API or integration"),
    ("other", "Other"),
]

TECHNOLOGIES = [
    ("", "Choose a preference"),
    ("Python / Flask", "Python / Flask"),
    ("JavaScript", "JavaScript"),
    ("React", "React"),
    ("PHP", "PHP"),
    ("Java", "Java"),
    (".NET", ".NET"),
    (
        "AI / Machine Learning frameworks",
        "AI / Machine Learning frameworks",
    ),
    ("Other technology", "Other technology"),
    (
        "Recommend a suitable technology",
        "Recommend a suitable technology",
    ),
]


# --------------------------------------------------
# Email Validation
# --------------------------------------------------

def valid_email(form, field):
    value = (field.data or "").strip()

    if (
        value.count("@") != 1
        or value.startswith("@")
        or value.endswith("@")
        or "." not in value.rsplit("@", 1)[1]
    ):
        raise ValidationError("Please enter a valid email address.")


# --------------------------------------------------
# Project Inquiry Form
# --------------------------------------------------

class InquiryForm(FlaskForm):
    name = StringField(
        "Full name",
        validators=[DataRequired(), Length(max=100)],
    )

    email = StringField(
        "Email address",
        validators=[DataRequired(), valid_email, Length(max=254)],
    )

    phone = StringField(
        "Phone number",
        validators=[Optional(), Length(max=40)],
    )

    company = StringField(
        "Company or organization",
        validators=[Optional(), Length(max=120)],
    )

    project_type = SelectField(
        "Project type",
        choices=PROJECT_TYPES,
        validators=[DataRequired()],
    )

    other_project = StringField(
        "Tell us the project type",
        validators=[Optional(), Length(max=100)],
    )

    description = TextAreaField(
        "Project description and requirements",
        validators=[DataRequired(), Length(min=20, max=4000)],
    )

    technology = SelectField(
        "Preferred technology",
        choices=TECHNOLOGIES,
        validators=[DataRequired()],
    )

    other_technology = StringField(
        "Specify the technology",
        validators=[Optional(), Length(max=100)],
    )

    budget = StringField(
        "Budget range",
        validators=[Optional(), Length(max=100)],
    )

    timeline = StringField(
        "Desired timeline",
        validators=[Optional(), Length(max=100)],
    )

    recommendations = BooleanField(
        "I'd like technology recommendations"
    )

    consent = BooleanField(
        "I consent to Knowledge Tech Solutions processing this inquiry.",
        validators=[
            DataRequired(
                message="Consent is required to submit your inquiry."
            )
        ],
    )

    # Honeypot field to help detect automated submissions.
    website = StringField(
        "Leave this field empty",
        validators=[
            Optional(),
            Length(
                max=0,
                message="Submission could not be accepted.",
            ),
        ],
    )


# --------------------------------------------------
# Flask Application Factory
# --------------------------------------------------

def create_app(test_config=None):

    # Vercel's writable temporary directory.
    # Local development uses the project's instance directory.
    if os.getenv("VERCEL") or os.getenv("VERCEL_ENV"):
        instance_path = "/tmp/knowledge-tech-solutions"
    else:
        instance_path = str(BASE_DIR / "instance")

    app = Flask(
    __name__,
    template_folder=str(BASE_DIR / "templates"),
    static_folder=str(BASE_DIR / "static"),
    instance_path=instance_path,
    instance_relative_config=True,
)

    app.config.from_mapping(
        SECRET_KEY=os.getenv(
            "SECRET_KEY",
            "development-only-change-this-key",
        ),
        MAX_CONTENT_LENGTH=32 * 1024,
        BUSINESS_EMAIL=os.getenv(
            "BUSINESS_EMAIL",
            "ktechsolutions@gmail.com",
        ),
        SMTP_HOST=os.getenv("SMTP_HOST", ""),
        SMTP_PORT=int(os.getenv("SMTP_PORT", "587")),
        SMTP_USERNAME=os.getenv("SMTP_USERNAME", ""),
        SMTP_PASSWORD=os.getenv("SMTP_PASSWORD", ""),
        MAIL_DEFAULT_SENDER=os.getenv("MAIL_DEFAULT_SENDER", ""),
        STORE_INQUIRIES=(
            os.getenv("STORE_INQUIRIES", "true").lower() == "true"
        ),
        SESSION_COOKIE_SECURE=(
            os.getenv("SESSION_COOKIE_SECURE", "false").lower()
            == "true"
        ),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
    )

    if test_config:
        app.config.update(test_config)

    Path(app.instance_path).mkdir(parents=True, exist_ok=True)

    CSRFProtect(app)
    logging.basicConfig(level=logging.INFO)

    # --------------------------------------------------
    # Template Context
    # --------------------------------------------------

    @app.context_processor
    def inject_year():
        return {"year": datetime.now().year}

    # --------------------------------------------------
    # Homepage
    # --------------------------------------------------

    @app.get("/")
    def index():
        form = InquiryForm()

        selected = request.args.get("service", "")

        if selected in dict(PROJECT_TYPES):
            form.project_type.data = selected

        return render_template("index.html", form=form)

    # --------------------------------------------------
    # Privacy Page
    # --------------------------------------------------

    @app.get("/privacy")
    def privacy():
        return render_template("privacy.html")

    # --------------------------------------------------
    # Project Inquiry Submission
    # --------------------------------------------------

    @app.post("/inquiry")
    def inquiry():
        form = InquiryForm()
        valid = form.validate()

        if (
            form.project_type.data == "other"
            and not (form.other_project.data or "").strip()
        ):
            form.other_project.errors.append(
                "Please describe the project type."
            )
            valid = False

        if (
            form.technology.data == "Other technology"
            and not (form.other_technology.data or "").strip()
        ):
            form.other_technology.errors.append(
                "Please specify the technology."
            )
            valid = False

        if not valid:
            flash(
                "Please correct the highlighted fields and try again.",
                "error",
            )
            return render_template("index.html", form=form), 400

        data = {
            key: value.strip() if isinstance(value, str) else value
            for key, value in form.data.items()
            if key not in {"csrf_token", "website"}
        }

        # Save the inquiry when storage is enabled.
        if app.config["STORE_INQUIRIES"]:
            save_inquiry(app, data, "pending")

        # Send the inquiry to the business email.
        try:
            send_email(app, data)

        except (OSError, smtplib.SMTPException) as exc:
            app.logger.warning(
                "Inquiry email delivery failed: %s",
                type(exc).__name__,
            )

            flash(
                "We could not send your inquiry just now. "
                "Please email ktechsolutions@gmail.com "
                "or message us on WhatsApp.",
                "error",
            )

            return render_template("index.html", form=form), 503

        flash(
            "Thank you — your inquiry was sent. "
            "We'll be in touch soon.",
            "success",
        )

        return redirect(url_for("index") + "#contact")

    return app


# --------------------------------------------------
# SQLite Inquiry Storage
# --------------------------------------------------

def save_inquiry(app, data, status):
    db_path = Path(app.instance_path) / "inquiries.sqlite"

    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS inquiries (
                id INTEGER PRIMARY KEY,
                created_at TEXT,
                name TEXT,
                email TEXT,
                phone TEXT,
                company TEXT,
                project_type TEXT,
                description TEXT,
                technology TEXT,
                budget TEXT,
                timeline TEXT,
                recommendations INTEGER,
                status TEXT
            )
            """
        )

        conn.execute(
            """
            INSERT INTO inquiries (
                created_at,
                name,
                email,
                phone,
                company,
                project_type,
                description,
                technology,
                budget,
                timeline,
                recommendations,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                datetime.now(timezone.utc).isoformat(),
                data["name"],
                data["email"],
                data["phone"],
                data["company"],
                data["project_type"],
                data["description"],
                data["technology"],
                data["budget"],
                data["timeline"],
                int(bool(data["recommendations"])),
                status,
            ),
        )


# --------------------------------------------------
# Email Delivery Using Gmail SMTP
# --------------------------------------------------

def send_email(app, data):
    required_settings = (
        "SMTP_HOST",
        "SMTP_USERNAME",
        "SMTP_PASSWORD",
        "MAIL_DEFAULT_SENDER",
    )

    if not all(app.config[key] for key in required_settings):
        raise smtplib.SMTPException(
            "SMTP is not configured. Check Vercel environment variables."
        )

    message = EmailMessage()

    message["Subject"] = (
        f"New project inquiry — {data['project_type']}"
    )
    message["From"] = app.config["MAIL_DEFAULT_SENDER"]
    message["To"] = app.config["BUSINESS_EMAIL"]
    message["Reply-To"] = data["email"]

    fields = [
        ("Name", data["name"]),
        ("Email", data["email"]),
        ("Phone", data["phone"] or "—"),
        ("Company", data["company"] or "—"),
        ("Project type", data["project_type"]),
        ("Technology", data["technology"]),
        ("Budget", data["budget"] or "—"),
        ("Timeline", data["timeline"] or "—"),
        (
            "Recommendations",
            "Yes" if data["recommendations"] else "No",
        ),
        ("Description", data["description"]),
    ]

    # Plain-text email body.
    text_body = "\n".join(
        f"{label}: {value}"
        for label, value in fields
    )

    message.set_content(text_body)

    # HTML email body.
    html_body = "".join(
        "<p><strong>"
        f"{html.escape(label)}:"
        "</strong> "
        f"{html.escape(str(value)).replace(chr(10), '<br>')}"
        "</p>"
        for label, value in fields
    )

    message.add_alternative(
        f"<h2>New project inquiry</h2>{html_body}",
        subtype="html",
    )

    with smtplib.SMTP(
        app.config["SMTP_HOST"],
        app.config["SMTP_PORT"],
        timeout=12,
    ) as server:
        server.starttls()

        server.login(
            app.config["SMTP_USERNAME"],
            app.config["SMTP_PASSWORD"],
        )

        server.send_message(message)


# --------------------------------------------------
# Vercel Flask Entry Point
# IMPORTANT: Keep this at the top level of app.py.
# --------------------------------------------------

app = create_app()


# Local development entry point.
if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False,
    )
