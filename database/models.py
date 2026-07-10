from datetime import datetime

from sqlalchemy import (
    BigInteger,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Boolean,
)
from sqlalchemy.orm import mapped_column, relationship

from .base import Base


class User(Base):
    __tablename__ = "users"

    id = mapped_column(BigInteger, primary_key=True)
    balance = mapped_column(Numeric(12, 2), default=1)
    is_banned = mapped_column(Boolean, default=False)
    mining_per_hour = mapped_column(Integer, default=1)
    is_mining = mapped_column(Boolean, default=False)

    referral = relationship(
        "Referral",
        back_populates="user",
        foreign_keys="Referral.user_id",
    )

    transaction = relationship(
        "Transaction",
        back_populates="user",
        foreign_keys="Transaction.user_id",
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


class Transaction(Base):
    __tablename__ = "transaction"

    id = mapped_column(BigInteger, primary_key=True)
    user_id = mapped_column(BigInteger, ForeignKey("users.id"))
    type = mapped_column(String)
    amount = mapped_column(Numeric(12, 2))
    time = mapped_column(DateTime, default=datetime.utcnow)

    user = relationship(
        "User",
        back_populates="transaction",
        foreign_keys=[user_id],
    )
