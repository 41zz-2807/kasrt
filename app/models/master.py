from datetime import date as date_cls, datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, Date, DateTime, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class House(db.Model):
    __tablename__ = "houses"
    __table_args__ = (UniqueConstraint("blok", "nomor", name="uq_houses_bloc_nomor"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    blok: Mapped[str] = mapped_column(String(8), nullable=False)
    nomor: Mapped[str] = mapped_column(String(8), nullable=False)
    nama_penghuni: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    start_period: Mapped[Optional[date_cls]] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    def __repr__(self) -> str:
        return f"<House {self.blok}/{self.nomor}>"


class DuesType(db.Model):
    __tablename__ = "dues_types"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nama: Mapped[str] = mapped_column(String(120), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class DuesRate(db.Model):
    __tablename__ = "dues_rates"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    dues_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    nominal: Mapped[int] = mapped_column(Integer, nullable=False)
    effective_period: Mapped[str] = mapped_column(String(7), nullable=False)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)

    def __repr__(self) -> str:
        return f"<DuesRate {self.effective_period} {self.nominal}>"


class Category(db.Model):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    nama: Mapped[str] = mapped_column(String(120), nullable=False)
    jenis: Mapped[str] = mapped_column(String(20), nullable=False, default="masuk")
    is_system: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)


class Setting(db.Model):
    __tablename__ = "settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    key: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(String(255), nullable=False, default="")
