from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

# Tasas de conversión aproximadas a ARS (valor en ARS por 1 unidad de moneda extranjera)
# Estas tasas deben actualizarse manualmente según la cotización vigente
EXCHANGE_RATES = {
    "USD": 1200.0,   # Dólar estadounidense
    "UYU": 28.0,     # Peso uruguayo
    "CLP": 1.3,      # Peso chileno
    "COP": 0.28,     # Peso colombiano
    "ARS": 1.0,      # Peso argentino (identidad)
}


def convert_to_another_currency(amount: float, from_currency: str, to_currency: str = "ARS") -> tuple[float, float]:
    """
    Convierte un monto en moneda extranjera a la moneda de destino.
    
    Args:
        amount: Monto en la moneda origen
        from_currency: Código de moneda (USD, UYU, CLP, COP, ARS)
        to_currency: Código de moneda (USD, UYU, CLP, COP, ARS)
    
    Returns:
        Tupla (monto_en_destino, tasa_usada)
    
    Raises:
        ValueError: Si la moneda no está soportada
    """
    currency_upper = from_currency.upper()
    if currency_upper not in EXCHANGE_RATES:
        raise ValueError(
            f"Moneda '{from_currency}' no soportada. "
            f"Monedas disponibles: {', '.join(EXCHANGE_RATES.keys())}"
        )
    
    if to_currency.upper() not in EXCHANGE_RATES:
        raise ValueError(
            f"Moneda '{to_currency}' no soportada. "
            f"Monedas disponibles: {', '.join(EXCHANGE_RATES.keys())}"
        )
    
    rate = EXCHANGE_RATES[currency_upper] / EXCHANGE_RATES[to_currency.upper()]
    amount_destiny = amount * rate
    logger.debug("Conversión: %.2f %s → %.2f %s (tasa: %.2f)", amount, currency_upper, amount_destiny, to_currency, rate)
    return (amount_destiny, rate)


def get_rates() -> dict[str, float]:
    """
    Retorna el diccionario de tasas de cambio vigentes.
    Útil para que el usuario consulte las tasas actuales.
    """
    return EXCHANGE_RATES.copy()


def is_supported_currency(currency: str) -> bool:
    """Verifica si una moneda está soportada para conversión."""
    return currency.upper() in EXCHANGE_RATES
