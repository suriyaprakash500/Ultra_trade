"""
Trading Autopilot — Technical Analysis Engine.

Calculates standard technical indicators using yfinance historical data:
- RSI (Relative Strength Index)
- MACD (Moving Average Convergence Divergence)
- Bollinger Bands
- Moving Averages (SMA 20, 50, 200 & EMA 12, 26)
- Volume analysis
- Support & Resistance levels
"""

from __future__ import annotations

from typing import Optional

import numpy as np
import yfinance as yf
from loguru import logger


def _safe_round(val, decimals=2):
    """Round a value safely, handling NaN/None."""
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return round(float(val), decimals)


class TechnicalAnalyzer:
    """Calculate technical indicators for Indian stocks via yfinance."""

    def __init__(self, symbol: str, period: str = "6mo"):
        self.symbol = symbol
        self.yf_symbol = f"{symbol}.NS"  # NSE suffix for yfinance
        self.period = period
        self._df = None

    def _fetch_data(self):
        """Fetch historical data from yfinance."""
        if self._df is not None:
            return self._df

        try:
            ticker = yf.Ticker(self.yf_symbol)
            self._df = ticker.history(period=self.period)
            if self._df.empty:
                logger.warning(f"No data for {self.yf_symbol}")
                return None
            return self._df
        except Exception as exc:
            logger.error(f"Failed to fetch data for {self.yf_symbol}: {exc}")
            return None

    # ── RSI ─────────────────────────────────────────────────────────

    def calculate_rsi(self, period: int = 14) -> Optional[float]:
        """Calculate Relative Strength Index."""
        df = self._fetch_data()
        if df is None or len(df) < period + 1:
            return None

        close = df["Close"]
        delta = close.diff()

        gain = delta.where(delta > 0, 0.0)
        loss = (-delta).where(delta < 0, 0.0)

        avg_gain = gain.rolling(window=period, min_periods=period).mean()
        avg_loss = loss.rolling(window=period, min_periods=period).mean()

        # Use Wilder's smoothing after initial SMA
        for i in range(period, len(avg_gain)):
            avg_gain.iloc[i] = (avg_gain.iloc[i - 1] * (period - 1) + gain.iloc[i]) / period
            avg_loss.iloc[i] = (avg_loss.iloc[i - 1] * (period - 1) + loss.iloc[i]) / period

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return _safe_round(rsi.iloc[-1])

    # ── MACD ────────────────────────────────────────────────────────

    def calculate_macd(self) -> dict:
        """Calculate MACD, Signal line, and Histogram."""
        df = self._fetch_data()
        if df is None or len(df) < 35:
            return {"macd": None, "signal": None, "histogram": None}

        close = df["Close"]

        ema_12 = close.ewm(span=12, adjust=False).mean()
        ema_26 = close.ewm(span=26, adjust=False).mean()

        macd_line = ema_12 - ema_26
        signal_line = macd_line.ewm(span=9, adjust=False).mean()
        histogram = macd_line - signal_line

        return {
            "macd": _safe_round(macd_line.iloc[-1]),
            "signal": _safe_round(signal_line.iloc[-1]),
            "histogram": _safe_round(histogram.iloc[-1]),
            "trend": "bullish" if histogram.iloc[-1] > 0 else "bearish",
        }

    # ── Bollinger Bands ─────────────────────────────────────────────

    def calculate_bollinger_bands(self, period: int = 20, std_dev: float = 2.0) -> dict:
        """Calculate Bollinger Bands."""
        df = self._fetch_data()
        if df is None or len(df) < period:
            return {"upper": None, "middle": None, "lower": None, "width": None}

        close = df["Close"]
        sma = close.rolling(window=period).mean()
        std = close.rolling(window=period).std()

        upper = sma + (std * std_dev)
        lower = sma - (std * std_dev)

        current_price = close.iloc[-1]
        bb_width = ((upper.iloc[-1] - lower.iloc[-1]) / sma.iloc[-1]) * 100

        # Position within bands (0% = lower, 100% = upper)
        bb_position = ((current_price - lower.iloc[-1]) / (upper.iloc[-1] - lower.iloc[-1])) * 100

        return {
            "upper": _safe_round(upper.iloc[-1]),
            "middle": _safe_round(sma.iloc[-1]),
            "lower": _safe_round(lower.iloc[-1]),
            "width": _safe_round(bb_width),
            "position_pct": _safe_round(bb_position),
        }

    # ── Moving Averages ─────────────────────────────────────────────

    def calculate_moving_averages(self) -> dict:
        """Calculate SMA 20/50/200 and EMA 12/26."""
        df = self._fetch_data()
        if df is None or len(df) < 10:
            return {}

        close = df["Close"]
        current = float(close.iloc[-1])

        sma_20 = _safe_round(close.rolling(20).mean().iloc[-1]) if len(df) >= 20 else None
        sma_50 = _safe_round(close.rolling(50).mean().iloc[-1]) if len(df) >= 50 else None
        sma_200 = _safe_round(close.rolling(200).mean().iloc[-1]) if len(df) >= 200 else None

        ema_12 = _safe_round(close.ewm(span=12).mean().iloc[-1])
        ema_26 = _safe_round(close.ewm(span=26).mean().iloc[-1])

        # Determine trend from MAs
        trend = "neutral"
        if sma_50 and sma_200:
            if sma_50 > sma_200:
                trend = "bullish"  # Golden cross territory
            else:
                trend = "bearish"  # Death cross territory

        return {
            "sma_20": sma_20,
            "sma_50": sma_50,
            "sma_200": sma_200,
            "ema_12": ema_12,
            "ema_26": ema_26,
            "current_price": _safe_round(current),
            "above_sma_20": current > sma_20 if sma_20 else None,
            "above_sma_50": current > sma_50 if sma_50 else None,
            "above_sma_200": current > sma_200 if sma_200 else None,
            "trend": trend,
        }

    # ── Volume Analysis ─────────────────────────────────────────────

    def calculate_volume_analysis(self) -> dict:
        """Analyze volume patterns."""
        df = self._fetch_data()
        if df is None or len(df) < 20:
            return {}

        volume = df["Volume"]

        avg_volume_20 = volume.rolling(20).mean().iloc[-1]
        current_volume = volume.iloc[-1]
        volume_ratio = current_volume / avg_volume_20 if avg_volume_20 > 0 else 1.0

        return {
            "current_volume": int(current_volume),
            "avg_volume_20d": int(avg_volume_20),
            "volume_ratio": _safe_round(volume_ratio),
            "volume_trend": "high" if volume_ratio > 1.5 else "normal" if volume_ratio > 0.7 else "low",
        }

    # ── Support & Resistance ────────────────────────────────────────

    def calculate_support_resistance(self) -> dict:
        """Find basic support and resistance levels from recent pivots."""
        df = self._fetch_data()
        if df is None or len(df) < 20:
            return {"support": None, "resistance": None}

        high = df["High"]
        low = df["Low"]
        close = df["Close"]

        # Recent 20-day high/low
        resistance = _safe_round(high.tail(20).max())
        support = _safe_round(low.tail(20).min())

        # Pivot point
        last_high = float(high.iloc[-1])
        last_low = float(low.iloc[-1])
        last_close = float(close.iloc[-1])
        pivot = (last_high + last_low + last_close) / 3

        return {
            "support": support,
            "resistance": resistance,
            "pivot": _safe_round(pivot),
            "r1": _safe_round(2 * pivot - last_low),
            "s1": _safe_round(2 * pivot - last_high),
        }

    # ── Full Analysis ───────────────────────────────────────────────

    def full_analysis(self) -> dict:
        """Run all technical indicators and return a complete analysis."""
        rsi = self.calculate_rsi()
        macd = self.calculate_macd()
        bb = self.calculate_bollinger_bands()
        ma = self.calculate_moving_averages()
        volume = self.calculate_volume_analysis()
        sr = self.calculate_support_resistance()

        # Generate overall signal
        signals = []
        if rsi is not None:
            if rsi < 30:
                signals.append("oversold")
            elif rsi > 70:
                signals.append("overbought")
            else:
                signals.append("neutral_rsi")

        if macd.get("trend") == "bullish":
            signals.append("macd_bullish")
        elif macd.get("trend") == "bearish":
            signals.append("macd_bearish")

        if ma.get("trend") == "bullish":
            signals.append("ma_bullish")
        elif ma.get("trend") == "bearish":
            signals.append("ma_bearish")

        if bb.get("position_pct") is not None:
            if bb["position_pct"] < 10:
                signals.append("near_lower_band")
            elif bb["position_pct"] > 90:
                signals.append("near_upper_band")

        # Determine overall signal
        bullish = sum(1 for s in signals if "bullish" in s or "oversold" in s or "near_lower" in s)
        bearish = sum(1 for s in signals if "bearish" in s or "overbought" in s or "near_upper" in s)

        if bullish > bearish:
            overall = "bullish"
            strength = min(bullish * 25, 100)
        elif bearish > bullish:
            overall = "bearish"
            strength = min(bearish * 25, 100)
        else:
            overall = "neutral"
            strength = 50

        return {
            "symbol": self.symbol,
            "rsi": rsi,
            "macd": macd,
            "bollinger_bands": bb,
            "moving_averages": ma,
            "volume": volume,
            "support_resistance": sr,
            "signals": signals,
            "overall_signal": overall,
            "signal_strength": strength,
        }


async def get_technical_analysis(symbol: str, period: str = "6mo") -> dict:
    """Convenience function to get full technical analysis."""
    analyzer = TechnicalAnalyzer(symbol, period)
    return analyzer.full_analysis()
