from datetime import datetime, timezone

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Numeric,
    Boolean,
    String,
)
from sqlalchemy.orm import mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = mapped_column(BigInteger, primary_key=True)
    balance = mapped_column(Numeric(12, 4), default=0)
    is_banned = mapped_column(Boolean, default=False)
    mining_per_hour = mapped_column(Numeric(8, 4), default=1)
    is_mining = mapped_column(Boolean, default=False)
    mining_started_at = mapped_column(DateTime(timezone=True), nullable=True)
    mining_speed_snapshot = mapped_column(Numeric(8, 4), nullable=True)
    last_activity_at = mapped_column(DateTime(timezone=True), nullable=True)
    last_miner_warning_at = mapped_column(DateTime(timezone=True), nullable=True)
    boost_active = mapped_column(Boolean, default=False)
    boost_expires_at = mapped_column(DateTime(timezone=True), nullable=True)

    referral = relationship(
        "Referral",
        back_populates="user",
        foreign_keys="Referral.user_id",
    )


class Referral(Base):
    __tablename__ = "referral"

    id = mapped_column(BigInteger, primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.id"))
    referral_id = mapped_column(BigInteger)
    is_active = mapped_column(Boolean, default=False)

    user = relationship(
        "User",
        back_populates="referral",
        foreign_keys=[user_id],
    )


class WithdrawRequest(Base):
    __tablename__ = "withdraw_requests"

    id = mapped_column(BigInteger, primary_key=True, autoincrement=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.id"))
    username = mapped_column(String)
    amount = mapped_column(Numeric(12, 4))
    status = mapped_column(String(20), default="pending")
    created_at = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    processed_at = mapped_column(DateTime(timezone=True), nullable=True)

    user = relationship("User")
