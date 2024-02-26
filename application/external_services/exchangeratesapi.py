import httpx
import os
import logging
from dotenv import load_dotenv
load_dotenv()
logging.basicConfig(level=logging.INFO)

exchangeratesapi_key = '04f4c6139e062d3fc7b9387ff217f70e' #os.getenv("EXCHANGE_RATES_API_KEY")

async def fetch_exchange_rates():
    """
    Response:
            {
            "success": true,
            "timestamp": 1519296206,
            "base": "EUR",
            "date": "2021-03-17",
            "rates": {
                "AUD": 1.566015,
                "CAD": 1.560132,
                "CHF": 1.154727,
                "CNY": 7.827874,
                "GBP": 0.882047,
                "JPY": 132.360679,
                "USD": 1.23396,
                [...]
                }
            }
    """
    # with subscription have access to https
    url = f"http://api.exchangeratesapi.io/v1/latest?access_key={exchangeratesapi_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(f"fetch_exchange_rates: {response}")
        return response.json()  

async def fetch_exchange_symbols():
    """
    Response:
            {
            "success": true,
            "symbols": {
                "AED": "United Arab Emirates Dirham",
                "AFN": "Afghan Afghani",
                "ALL": "Albanian Lek",
                "AMD": "Armenian Dram",
                [...]
                }
            }
    """
    # with subscription have access to https
    url = f"http://api.exchangeratesapi.io/v1/symbols?access_key={exchangeratesapi_key}"
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        print(f"fetch_exchange_symbols: {response}")
        return response.json()      
