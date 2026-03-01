"""
Trading Autopilot — Market Data Tools (Yahoo Finance).

Uses Yahoo Finance as a free fallback for market data since the free
Kite Connect personal API doesn't include market data access.
"""

from __future__ import annotations

from loguru import logger


async def fetch_stock_price(symbol: str) -> dict:
    """
    Fetch current price and basic info for an NSE stock.

    Appends ".NS" suffix for Yahoo Finance NSE lookup.

    Args:
        symbol: NSE stock symbol (e.g. "RELIANCE")

    Returns:
        dict with current_price, day_high, day_low, volume, etc.
    """
    try:
        import yfinance as yf

        # Yahoo Finance uses .NS suffix for NSE stocks
        yf_symbol = f"{symbol.upper()}.NS"
        ticker = yf.Ticker(yf_symbol)
        info = ticker.info

        result = {
            "symbol": symbol.upper(),
            "exchange": "NSE",
            "current_price": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "previous_close": info.get("previousClose", 0),
            "open": info.get("open", info.get("regularMarketOpen", 0)),
            "day_high": info.get("dayHigh", info.get("regularMarketDayHigh", 0)),
            "day_low": info.get("dayLow", info.get("regularMarketDayLow", 0)),
            "volume": info.get("volume", info.get("regularMarketVolume", 0)),
            "market_cap": info.get("marketCap", 0),
            "pe_ratio": info.get("trailingPE", 0),
            "sector": info.get("sector", "unknown"),
            "industry": info.get("industry", "unknown"),
            "52_week_high": info.get("fiftyTwoWeekHigh", 0),
            "52_week_low": info.get("fiftyTwoWeekLow", 0),
            "beta": info.get("beta", 1.0),
        }

        # Calculate change
        if result["previous_close"] and result["current_price"]:
            result["change"] = round(
                result["current_price"] - result["previous_close"], 2
            )
            result["change_pct"] = round(
                (result["change"] / result["previous_close"]) * 100, 2
            )
        else:
            result["change"] = 0
            result["change_pct"] = 0

        logger.info(
            f"Price fetched: {symbol} = ₹{result['current_price']:,.2f} "
            f"({result['change_pct']:+.2f}%)"
        )
        return result

    except Exception as exc:
        logger.error(f"Failed to fetch price for {symbol}: {exc}")
        return {
            "symbol": symbol.upper(),
            "error": str(exc),
            "current_price": 0,
        }


async def fetch_stock_history(
    symbol: str, period: str = "1mo"
) -> dict:
    """
    Fetch historical OHLCV data for a stock.

    Args:
        symbol: NSE stock symbol
        period: Time period ("1d", "5d", "1mo", "3mo", "6mo", "1y")

    Returns:
        dict with dates and OHLCV arrays.
    """
    valid_periods = {"1d", "5d", "1mo", "3mo", "6mo", "1y", "2y", "5y"}
    if period not in valid_periods:
        period = "1mo"

    try:
        import yfinance as yf

        yf_symbol = f"{symbol.upper()}.NS"
        ticker = yf.Ticker(yf_symbol)
        hist = ticker.history(period=period)

        if hist.empty:
            return {"symbol": symbol, "error": "No data available", "data": []}

        data = []
        for date, row in hist.iterrows():
            data.append({
                "date": date.strftime("%Y-%m-%d"),
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(row["Volume"]),
            })

        # Calculate volatility (annualized std dev of daily returns)
        if len(data) >= 5:
            import numpy as np
            closes = [d["close"] for d in data]
            returns = np.diff(np.log(closes))
            volatility = float(np.std(returns, ddof=1) * np.sqrt(252) * 100)
        else:
            volatility = 0.0

        result = {
            "symbol": symbol.upper(),
            "period": period,
            "data_points": len(data),
            "data": data,
            "latest_close": data[-1]["close"] if data else 0,
            "period_high": max(d["high"] for d in data) if data else 0,
            "period_low": min(d["low"] for d in data) if data else 0,
            "annualized_volatility": round(volatility, 2),
        }

        logger.info(
            f"History fetched: {symbol} ({period}), "
            f"{len(data)} data points, "
            f"volatility: {volatility:.1f}%"
        )
        return result

    except Exception as exc:
        logger.error(f"Failed to fetch history for {symbol}: {exc}")
        return {"symbol": symbol, "error": str(exc), "data": []}


async def fetch_multiple_prices(symbols: list[str]) -> dict[str, float]:
    """
    Fetch current prices for multiple symbols.

    Returns a dict of {symbol: current_price}.
    Useful for updating paper trading positions.
    """
    prices: dict[str, float] = {}

    for symbol in symbols:
        try:
            result = await fetch_stock_price(symbol)
            price = result.get("current_price", 0)
            if price > 0:
                prices[symbol] = price
        except Exception as exc:
            logger.warning(f"Price fetch failed for {symbol}: {exc}")

    return prices


async def fetch_technical_indicators(symbol: str) -> dict:
    """
    Get RSI, MACD, Bollinger Bands, MAs, and support/resistance for a stock.

    Used by the AI agent to make better trade decisions.
    """
    from backend.ai.technical_analysis import get_technical_analysis
    return await get_technical_analysis(symbol.upper())
