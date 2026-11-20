import logging
import time

from app import create_app

log = logging.getLogger("kasrt-worker")


def run_cycle() -> None:
    """One worker cycle: monthly invoice generation + email outbox drain."""
    app = create_app()
    with app.app_context():
        log.info("worker cycle")


def main() -> None:
    log.info("kasrt worker started")
    while True:
        run_cycle()
        time.sleep(60)


if __name__ == "__main__":
    main()
