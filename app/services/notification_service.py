import smtplib
from email.mime.text import MIMEText

from app.config import Config
from app.extensions import db
from app.models.notification import NotificationOutbox

MAX_ATTEMPTS = 5
SMTP_TIMEOUT = 10


def create_outbox(to_email: str, subject: str, body: str) -> NotificationOutbox:
    row = NotificationOutbox(to_email=to_email, subject=subject, body=body, status="pending")
    db.session.add(row)
    db.session.commit()
    return row


def _send(to_email: str, subject: str, body: str) -> None:
    msg = MIMEText(body, "plain")
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_FROM
    msg["To"] = to_email
    with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=SMTP_TIMEOUT) as smtp:
        smtp.starttls()
        smtp.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
        smtp.sendmail(msg["From"], [to_email], msg.as_string())


def process_outbox(limit: int = 10) -> None:
    rows = NotificationOutbox.query.filter_by(status="pending").order_by(NotificationOutbox.id).limit(limit).all()
    for row in rows:
        row.attempts += 1
        try:
            _send(row.to_email, row.subject, row.body)
            row.status = "sent"
            row.sent_at = None
        except Exception as exc:  # noqa: BLE001
            if row.attempts >= MAX_ATTEMPTS:
                row.status = "failed"
            row.last_error = str(exc)
        db.session.commit()
