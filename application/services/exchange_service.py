from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet, Transaction, ExchangeRate
from application.dtos.wallet_dto import WalletOutDTO
from domain.repositories.transaction_repository import deposit_transaction, convert_currency
from sqlalchemy import update
from decimal import Decimal
from sqlalchemy import exc as sa_exc
import logging
logging.basicConfig(level=logging.INFO)

async def convert_funds(session: AsyncSession, amount: Decimal, from_currency: int, to_currency: int):
    exchange_res = await convert_currency(session, amount, from_currency, to_currency)
    logging.info(f"Exchange results in exchange service: {amount}")
    if not exchange_res:
        return None
    return exchange_res