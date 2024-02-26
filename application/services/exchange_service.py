from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from domain.models import Wallet, Transaction, ExchangeRate, Currency
from application.dtos.wallet_dto import WalletOutDTO
from domain.repositories.transaction_repository import convert_currency
from domain.repositories.exchange_repository import add_or_update_currency, update_or_create_exchange_rate, get_last_exchange_rate_update, get_exchange_rate
from application.external_services.exchangeratesapi import fetch_exchange_symbols, fetch_exchange_rates
from sqlalchemy import update
from decimal import Decimal
from sqlalchemy import exc as sa_exc
from datetime import datetime
import logging
logging.basicConfig(level=logging.INFO)

# This metod will proccess conversion by exchange rate in wallet and create transaction 
async def convert_funds(session: AsyncSession, amount: Decimal, from_currency: int, to_currency: int):
    exchange_res = await convert_currency(session, amount, from_currency, to_currency)
    logging.info(f"Exchange results in exchange service: {amount}")
    if not exchange_res:
        return None
    return exchange_res

# Method just for return exchange rate conversion result without change db
async def calculate_conversion(session: AsyncSession, from_currency_code: str, to_currency_code: str, amount: Decimal) -> Decimal:
    rate = await get_exchange_rate(session, from_currency_code, to_currency_code)
    if rate:
        converted_amount = amount * rate
        return converted_amount
    else:
        return None

# Method just for get last update date and time from db


async def get_last_update(session: AsyncSession) -> dict:
    last_update = await get_last_exchange_rate_update(session)
    if last_update:
        return last_update
    else:
        return {"error": "No exchange rates updates found"}


async def update_currencies_from_api(session: AsyncSession):
    """
    Updates the list of currencies in the database from the external API.
    """
    symbols_response = await fetch_exchange_symbols()
    if symbols_response.get("success"):
        symbols = symbols_response.get("symbols", {})
        try:
            for code, name in symbols.items():
                # Here we assume that the symbol and the code are the same, until for extension other api with real currency code
                await add_or_update_currency(session, name=name, symbol=code)  #code=code
            return True    
        except Exception as e:
            return e        
    else:
        logging.error("Failed to fetch currency symbols from the API")
        return None
    

async def update_exchange_rates(session: AsyncSession):
    """
    Updates the list of rates in the database from the external API.
    """
    rates_data = await fetch_exchange_rates() # here we can add base currency arg
    if rates_data.get("success"):
        timestamp = datetime.fromtimestamp(rates_data['timestamp'])
        base_currency_symbol = rates_data['base']
        rates = rates_data['rates']
        logging.info(f"rates: {rates}")
        # Обновляем курсы валют
        try:
            result = await update_or_create_exchange_rate(session, base_currency_symbol, rates, timestamp)
            if result:
                return True
            else:
                return False
        except Exception as e:
            return e  
    else:
        logging.error("Failed to fetch currency rates from the API")
        return None

