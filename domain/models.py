from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy import Enum as En
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from infrastructure.db.database import Base # infrastructure.db.database
from sqlalchemy import Column, Integer, String
from sqlalchemy.types import DECIMAL

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    wallets = relationship("Wallet", back_populates="owner")

class Wallet(Base):
    __tablename__ = 'wallets'
    id = Column(Integer, primary_key=True, index=True)
    balance = Column(DECIMAL(precision=20, scale=10))
    reserved_balance = Column(DECIMAL(precision=20, scale=10))
    currency_id = Column(Integer, ForeignKey('currencies.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="wallets")
    currency = relationship("Currency")


class TransactionType(str, En):
    TRANSFER = "transfer"
    RESERVE = "reserve"
    RELEASE = "release"
    WITHDRAW = "withdraw"
    DEPOSIT = "deposit"

class TransactionStatus(str, En):
    PROCESSING = "processing"
    CLOSE = "close"
    CANCEL = "cancel" 
    

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True, index=True)
    from_wallet_id = Column(Integer, ForeignKey('wallets.id'))
    from_currency_id = Column(Integer, ForeignKey('currencies.id'))
    amount = Column(DECIMAL(precision=20, scale=10)) 
    to_wallet_id = Column(Integer, ForeignKey('wallets.id'))
    to_currency_id = Column(Integer, ForeignKey('currencies.id'))
    rate = Column(DECIMAL(precision=20, scale=10))
    converted_amount = Column(DECIMAL(precision=20, scale=10)) 
    type = Column(String(50))
    status = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    

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
    rate = Column(DECIMAL(precision=20, scale=10))
#reverse_rate = Column(DECIMAL(precision=20, scale=10))
#timestamp = Column(DateTime(timezone=True), server_default=func.now())

