from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.extensions import db


class Invoice(db.Model):
    __tablename__ = "invoices"
    __table_args__ = (
        UniqueConstraint("house_id", "dues_type_id", "period", name="uq_invoices_house_type_period"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    house_id: Mapped[int] = mapped_column(Integer, nullable=False)
    dues_type_id: Mapped[int] = mapped_column(Integer, nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)
    nominal: Mapped[int] = mapped_column(Integer, nullable=False)
    paid_amount: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="belum")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )

    def __repr__(self) -> str:
        return f"<Invoice {self.house_id}/{self.dues_type_id}/{self.period}>"


class Transaction(db.Model):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    trx_no: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    tanggal: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    jenis: Mapped[str] = mapped_column(String(20), nullable=False)
    category_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    house_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    jumlah: Mapped[int] = mapped_column(Integer, nullable=False)
    keterangan: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="aktif")
    void_reason: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    voided_by: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    voided_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    receipt_no: Mapped[Optional[str]] = mapped_column(String(32), nullable=True)
    created_by: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None)
    )


class PaymentAllocation(db.Model):
    __tablename__ = "payment_allocations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    transaction_id: Mapped[int] = mapped_column(Integer, nullable=False)
    invoice_id: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)


class PeriodLock(db.Model):
    __tablename__ = "period_locks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    period: Mapped[str] = mapped_column(String(7), unique=True, nullable=False)
    locked_by: Mapped[int] = mapped_column(Integer, nullable=False)
    locked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
