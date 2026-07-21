from datetime import datetime, timezone

from sqlalchemy import (
    Integer,
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

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.id"))
    username = mapped_column(String)
    amount = mapped_column(Numeric(12, 4))
    status = mapped_column(String(20), default="pending")
    created_at = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    processed_at = mapped_column(DateTime(timezone=True), nullable=True)
    message_id = mapped_column(BigInteger, nullable=True)

    user = relationship("User")


class TrackingLink(Base):
    __tablename__ = "tracking_links"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_code = mapped_column(String(50), unique=True, nullable=False)
    name = mapped_column(String(255), nullable=False)
    created_at = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    total_starts = mapped_column(BigInteger, default=0)
    total_miners = mapped_column(BigInteger, default=0)


class TrackingEvent(Base):
    __tablename__ = "tracking_events"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    link_id = mapped_column(BigInteger, ForeignKey("tracking_links.id"))
    user_id = mapped_column(BigInteger, ForeignKey("users.id"))
    event_type = mapped_column(String(20))
    created_at = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    link = relationship("TrackingLink")
    user = relationship("User")


class Broadcast(Base):
    __tablename__ = "broadcasts"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)
    text = mapped_column(String, nullable=True)
    media_type = mapped_column(String(20), nullable=True)
    media_file_id = mapped_column(String, nullable=True)
    caption = mapped_column(String, nullable=True)
    button_text = mapped_column(String, nullable=True)
    button_url = mapped_column(String, nullable=True)
    target_group = mapped_column(String(20), default="all")
    created_at = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    sent_count = mapped_column(BigInteger, default=0)
    failed_count = mapped_column(BigInteger, default=0)
    status = mapped_column(String(20), default="pending")
