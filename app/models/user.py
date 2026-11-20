from datetime import datetime, timezone
from typing import Optional
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from flask_login import UserMixin
from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db

argon2 = PasswordHasher(time_cost=2, memory_cost=19456, parallelism=1)

ROLES = ("superuser", "ketua_rt", "bendahara", "warga")
STAFF_ROLES = ("superuser", "ketua_rt", "bendahara")
WRITE_ROLES = ("superuser", "bendahara")
DEFAULT_ROLE = "warga"
LOCKOUT_FAILS = 5
LOCKOUT_MINUTES = 15
MIN_PASSWORD_LENGTH = 10


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    email: Mapped[Optional[str]] = mapped_column(String(120), unique=True, nullable=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), nullable=False, default=DEFAULT_ROLE)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    must_change_password: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_login_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    def get_id(self) -> str:
        return str(self.id)

    def set_password(self, password: str) -> None:
        self.password_hash = argon2.hash(password)

    def check_password(self, password: str) -> bool:
        if not password:
            return False
        try:
            return argon2.verify(self.password_hash, password)
        except VerifyMismatchError:
            return False
