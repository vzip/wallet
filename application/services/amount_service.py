import logging
logging.basicConfig(level=logging.INFO)

from decimal import Decimal, ROUND_DOWN

def round_decimal(d, decimal_places=10):
    return d.quantize(Decimal(10) ** -decimal_places, rounding=ROUND_DOWN)

