from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet, Transaction, ExchangeRate, Currency, ServiceWallet, PendingTransaction, ExternalWallet
from application.dtos.wallet_dto import WalletListDTO, WalletOutDTO, WalletCreateDTO, ServiceWalletOutDTO, ServiceWalletListDTO
from application.dtos.transaction_dto import TransactionOutDTO
from domain.repositories.payments_repository import update_deposit_transaction, update_withdraw_transaction
from decimal import Decimal
from pydantic import parse_obj_as
from typing import List
import uuid
import logging
logging.basicConfig(level=logging.INFO)

async def update_service_deposit_transaction(session: AsyncSession, transaction_id: uuid.UUID, new_status: str, service_user_id: uuid.UUID):
    new_transaction_service = await update_deposit_transaction(session, transaction_id, new_status, service_user_id)
    logging.info(f"pending_transaction in service: {new_transaction_service.id}")
    if not new_transaction_service:
        return None
    return TransactionOutDTO(
        id=new_transaction_service.id,
        from_wallet_id=new_transaction_service.from_wallet_id,
        from_currency_id=new_transaction_service.from_currency_id,
        amount=new_transaction_service.amount,
        to_wallet_id=new_transaction_service.to_wallet_id,
        to_currency_id=new_transaction_service.to_currency_id,
        rate=new_transaction_service.rate,
        converted_amount=new_transaction_service.converted_amount,
        type=new_transaction_service.type,
        status=new_transaction_service.status,
        timestamp=new_transaction_service.timestamp,
        user_id=new_transaction_service.user_id,
        
    )

async def update_service_withdraw_transaction(session: AsyncSession, transaction_id: uuid.UUID, new_status: str, service_user_id: uuid.UUID):
    new_transaction_service = await update_withdraw_transaction(session, transaction_id, new_status, service_user_id)
    logging.info(f"pending_transaction in service: {new_transaction_service.id}")
    if not new_transaction_service:
        return None
    return TransactionOutDTO(
        id=new_transaction_service.id,
        from_wallet_id=new_transaction_service.from_wallet_id,
        from_currency_id=new_transaction_service.from_currency_id,
        amount=new_transaction_service.amount,
        to_wallet_id=new_transaction_service.to_wallet_id,
        to_currency_id=new_transaction_service.to_currency_id,
        rate=new_transaction_service.rate,
        converted_amount=new_transaction_service.converted_amount,
        type=new_transaction_service.type,
        status=new_transaction_service.status,
        timestamp=new_transaction_service.timestamp,
        user_id=new_transaction_service.user_id,
        
    )