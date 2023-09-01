from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from db.database import Base # infrastructure.db.database

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    wallets = relationship("Wallet", back_populates="owner")

class Wallet(Base):
    __tablename__ = 'wallets'
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(Float)
    currency_id = Column(Integer, ForeignKey('currencies.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="wallets")
    currency = relationship("Currency")


class TransactionType(Enum):
    TRANSFER = "transfer"
    RESERVE = "reserve"
    RELEASE = "release"
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"
    

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float)
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    from_wallet_id = Column(Integer, ForeignKey('wallets.id'))
    to_wallet_id = Column(Integer, ForeignKey('wallets.id'))
    type = Column(Enum(TransactionType))

class Currency(Base):
    __tablename__ = 'currencies'
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True)
    symbol = Column(String, unique=True)

class ExchangeRate(Base):
    __tablename__ = 'exchange_rates'
    id = Column(Integer, primary_key=True, index=True)
    from_currency_id = Column(Integer, ForeignKey('currencies.id'))
    to_currency_id = Column(Integer, ForeignKey('currencies.id'))
    rate = Column(Float)
