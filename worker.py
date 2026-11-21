import logging
import time

from app import create_app
from app.services import notification_service

log = logging.getLogger("kasrt-worker")


def run_cycle() -> None:
    """One worker cycle: email outbox drain + monthly invoice generation."""
    app = create_app()
    with app.app_context():
        notification_service.process_outbox()


def main() -> None:
    log.info("kasrt worker started")
    while True:
        run_cycle()
        time.sleep(60)


if __name__ == "__main__":
    main()
