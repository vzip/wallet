from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy import Enum as En
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from infrastructure.db.database import Base # infrastructure.db.database
from sqlalchemy import Column, Integer, String
from sqlalchemy.types import DECIMAL
from sqlalchemy.ext.declarative import declared_attr
import uuid


class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    wallets = relationship("Wallet", back_populates="owner")
    user_external_wallets = relationship("UserExternalWallet", back_populates="owner")

class ServiceUser(Base):
    __tablename__ = 'service_users'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    service_wallets = relationship("ServiceWallet", back_populates="owner")
    external_wallets = relationship("ExternalWallet", back_populates="owner")    

class Wallet(Base):
    __tablename__ = 'wallets'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    balance = Column(DECIMAL(precision=20, scale=10))
    reserved_balance = Column(DECIMAL(precision=20, scale=10))
    currency_id = Column(Integer, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    owner = relationship("User", back_populates="wallets")

class UserExternalWallet(Base):
    __tablename__ = 'user_external_wallets'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    wallet_name = Column(String, nullable=False)
    amount_withdraw = Column(DECIMAL(precision=20, scale=10))
    currency_id = Column(Integer, index=True)
    card_id = Column(UUID(as_uuid=True), nullable=True) 
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    owner = relationship("User", back_populates="user_external_wallets")
    

class UserExternalCards(Base):
    __tablename__ = 'user_external_cards'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    card_name = Column(String, nullable=False)
    currency_id = Column(Integer, index=True)
    bank_name = Column(String, nullable=False)
    card_name_holder = Column(String, nullable=False)
    card_16_digits = Column(String, nullable=False)
    card_expire_month = Column(Integer, nullable=False)
    card_expire_year = Column(Integer, nullable=False)
    card_type_provider = Column(String, nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    user_external_wallet_id = Column(UUID(as_uuid=True), ForeignKey('user_external_wallets.id'))


class ServiceWallet(Base):
    __tablename__ = 'service_wallets'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    balance = Column(DECIMAL(precision=20, scale=10))
    reserved_balance = Column(DECIMAL(precision=20, scale=10))
    currency_id = Column(Integer, index=True)
    commission_rate = Column(DECIMAL(precision=20, scale=10), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('service_users.id'))
    owner = relationship("ServiceUser", back_populates="service_wallets")   

class ExternalWallet(Base):
    __tablename__ = 'external_wallets'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    balance = Column(DECIMAL(precision=20, scale=10))
    reserved_balance = Column(DECIMAL(precision=20, scale=10))
    currency_id = Column(Integer, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey('service_users.id'))
    owner = relationship("ServiceUser", back_populates="external_wallets")       


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
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    from_wallet_id = Column(UUID(as_uuid=True), nullable=False)
    from_currency_id = Column(Integer, ForeignKey('currencies.id'))
    amount = Column(DECIMAL(precision=20, scale=10)) 
    to_wallet_id = Column(UUID(as_uuid=True), nullable=False)
    to_currency_id = Column(Integer, ForeignKey('currencies.id'))
    rate = Column(DECIMAL(precision=20, scale=10))
    converted_amount = Column(DECIMAL(precision=20, scale=10)) 
    type = Column(String(50))
    status = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(UUID(as_uuid=True), nullable=False)

class ServiceTransaction(Base):
    __tablename__ = 'service_transactions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    from_wallet_id = Column(UUID(as_uuid=True), nullable=False)
    from_currency_id = Column(Integer, ForeignKey('currencies.id'))
    amount = Column(DECIMAL(precision=20, scale=10)) 
    to_wallet_id = Column(UUID(as_uuid=True), nullable=False)
    to_currency_id = Column(Integer, ForeignKey('currencies.id'))
    rate = Column(DECIMAL(precision=20, scale=10))
    converted_amount = Column(DECIMAL(precision=20, scale=10)) 
    type = Column(String(50))
    status = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey('service_users.id'))    


class PendingTransaction(Base):
    # ... (остальные поля)
    __tablename__ = 'pending_transactions'
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, unique=True, nullable=False)
    from_wallet_id = Column(UUID(as_uuid=True), ForeignKey('service_wallets.id'))
    from_currency_id = Column(Integer, ForeignKey('currencies.id'))
    amount = Column(DECIMAL(precision=20, scale=10)) 
    to_wallet_id = Column(UUID(as_uuid=True), ForeignKey('wallets.id'))
    to_currency_id = Column(Integer, ForeignKey('currencies.id'))
    rate = Column(DECIMAL(precision=20, scale=10))
    converted_amount = Column(DECIMAL(precision=20, scale=10)) 
    type = Column(String(50))
    status = Column(String(50))
    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id'))
    external_wallet_id = Column(UUID(as_uuid=True), ForeignKey('external_wallets.id'))
    external_transaction_id = Column(UUID(as_uuid=True), unique=True)

    

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

