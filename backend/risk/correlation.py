"""
Trading Autopilot — Correlation Management.

Tracks correlation between portfolio positions to enforce diversification.
Highly correlated positions defeat the purpose of diversification.

Rule: Max 0.70 correlation between any two positions.
"""

from __future__ import annotations

from loguru import logger


# Predefined sector correlations for Indian markets (simplified)
# In production, compute from historical price data
SECTOR_CORRELATION_MAP: dict[tuple[str, str], float] = {
    ("IT", "IT"): 1.0,
    ("IT", "Banking"): 0.3,
    ("IT", "Pharma"): 0.2,
    ("IT", "Auto"): 0.4,
    ("IT", "FMCG"): 0.25,
    ("IT", "Energy"): 0.15,
    ("Banking", "Banking"): 1.0,
    ("Banking", "FMCG"): 0.35,
    ("Banking", "Auto"): 0.5,
    ("Banking", "Pharma"): 0.2,
    ("Banking", "Energy"): 0.4,
    ("Pharma", "Pharma"): 1.0,
    ("Pharma", "FMCG"): 0.4,
    ("Pharma", "Auto"): 0.15,
    ("Pharma", "Energy"): 0.1,
    ("Auto", "Auto"): 1.0,
    ("Auto", "FMCG"): 0.3,
    ("Auto", "Energy"): 0.45,
    ("FMCG", "FMCG"): 1.0,
    ("FMCG", "Energy"): 0.2,
    ("Energy", "Energy"): 1.0,
}

# Stock-to-sector mapping for major Indian stocks
STOCK_SECTOR_MAP: dict[str, str] = {
    # IT
    "TCS": "IT", "INFY": "IT", "WIPRO": "IT", "HCLTECH": "IT",
    "TECHM": "IT", "LTIM": "IT", "COFORGE": "IT",
    # Banking
    "HDFCBANK": "Banking", "ICICIBANK": "Banking", "KOTAKBANK": "Banking",
    "SBIN": "Banking", "AXISBANK": "Banking", "INDUSINDBK": "Banking",
    "BAJFINANCE": "Banking", "BAJAJFINSV": "Banking",
    # Pharma
    "SUNPHARMA": "Pharma", "DRREDDY": "Pharma", "CIPLA": "Pharma",
    "DIVISLAB": "Pharma", "APOLLOHOSP": "Pharma",
    # Auto
    "MARUTI": "Auto", "TATAMOTORS": "Auto", "M&M": "Auto",
    "BAJAJ-AUTO": "Auto", "HEROMOTOCO": "Auto", "EICHERMOT": "Auto",
    # FMCG
    "HINDUNILVR": "FMCG", "ITC": "FMCG", "NESTLEIND": "FMCG",
    "BRITANNIA": "FMCG", "DABUR": "FMCG", "GODREJCP": "FMCG",
    # Energy
    "RELIANCE": "Energy", "ONGC": "Energy", "NTPC": "Energy",
    "POWERGRID": "Energy", "ADANIENT": "Energy", "ADANIGREEN": "Energy",
    "COALINDIA": "Energy", "IOC": "Energy", "BPCL": "Energy",
    # Metals
    "TATASTEEL": "Metals", "HINDALCO": "Metals", "JSWSTEEL": "Metals",
    # Telecom
    "BHARTIARTL": "Telecom", "IDEA": "Telecom",
}


def get_sector(symbol: str) -> str:
    """Look up the sector for a given stock symbol."""
    return STOCK_SECTOR_MAP.get(symbol.upper(), "unknown")


def get_correlation(sector_a: str, sector_b: str) -> float:
    """
    Get the correlation coefficient between two sectors.

    Returns a value between 0.0 (uncorrelated) and 1.0 (perfectly correlated).
    """
    key = (sector_a, sector_b)
    reverse_key = (sector_b, sector_a)

    if key in SECTOR_CORRELATION_MAP:
        return SECTOR_CORRELATION_MAP[key]
    if reverse_key in SECTOR_CORRELATION_MAP:
        return SECTOR_CORRELATION_MAP[reverse_key]

    # Default: moderate correlation for unknown sectors
    if sector_a == sector_b:
        return 1.0
    return 0.35


def check_portfolio_correlation(
    existing_positions: list[dict],
    new_symbol: str,
    max_correlation: float = 0.70,
) -> dict:
    """
    Check if adding a new position would violate correlation limits.

    Args:
        existing_positions: List of position dicts with 'symbol' and 'sector'.
        new_symbol: Symbol of the proposed new position.
        max_correlation: Maximum allowed correlation (default 0.70).

    Returns:
        dict with 'allowed' bool and details of any violations.
    """
    new_sector = get_sector(new_symbol)
    violations: list[dict] = []

    for pos in existing_positions:
        pos_sector = pos.get("sector") or get_sector(pos.get("symbol", ""))
        corr = get_correlation(new_sector, pos_sector)

        if corr > max_correlation:
            violations.append({
                "existing_symbol": pos.get("symbol"),
                "existing_sector": pos_sector,
                "new_symbol": new_symbol,
                "new_sector": new_sector,
                "correlation": corr,
                "limit": max_correlation,
            })

    allowed = len(violations) == 0

    if not allowed:
        logger.warning(
            f"Correlation check failed for {new_symbol}: "
            f"{len(violations)} violation(s)"
        )

    return {
        "allowed": allowed,
        "new_symbol": new_symbol,
        "new_sector": new_sector,
        "violations": violations,
        "checked_against": len(existing_positions),
    }
