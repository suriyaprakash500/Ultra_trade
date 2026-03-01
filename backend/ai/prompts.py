"""
Trading Autopilot — Grok AI Prompt Templates.

Centralized prompt management for all AI interactions.
Each prompt is a function that takes context and returns a formatted string,
making it easy to iterate on prompt engineering.
"""

from __future__ import annotations


def news_sentiment_prompt(
    news_title: str,
    news_content: str,
    watchlist: list[str] | None = None,
) -> str:
    """
    Prompt for analyzing news sentiment and identifying affected stocks.

    Returns structured JSON from Grok.
    """
    watchlist_str = ", ".join(watchlist) if watchlist else "any Indian stocks"

    return f"""You are a senior financial analyst specializing in Indian equity markets (NSE/BSE).

Analyze the following news item and provide a structured assessment.

NEWS TITLE: {news_title}
NEWS CONTENT: {news_content}

WATCHLIST: {watchlist_str}

Respond with ONLY valid JSON in this exact format:
{{
    "sentiment": "very_bullish|bullish|neutral|bearish|very_bearish",
    "sentiment_score": <float from -2.0 to +2.0>,
    "impact_level": "critical|high|medium|low",
    "affected_symbols": ["SYMBOL1", "SYMBOL2"],
    "summary": "<one paragraph analysis>",
    "confidence": <float from 0 to 100>,
    "recommended_action": "buy|sell|hold|watch",
    "time_sensitivity": "immediate|today|this_week|long_term",
    "reasoning": "<brief reasoning for the assessment>"
}}

Rules:
- Only include symbols from NSE/BSE that are directly or indirectly affected
- Be conservative with confidence scores
- "critical" impact = market-wide or major sector shift
- "high" impact = significant single stock or sector movement
- Consider supply chain effects and competitor impact
- Indian market context: consider RBI policies, FII flows, domestic factors"""


def trade_idea_prompt(
    portfolio_summary: dict,
    news_analyses: list[dict],
    market_context: str = "",
    risk_params: dict | None = None,
) -> str:
    """
    Prompt for generating trade ideas based on portfolio and news.
    """
    risk_str = ""
    if risk_params:
        risk_str = f"""
RISK PARAMETERS:
- Max risk per trade: {risk_params.get('max_risk_pct', 2)}%
- Max position size: {risk_params.get('max_position_pct', 10)}% of portfolio
- Max positions: {risk_params.get('max_positions', 6)}
- Current positions: {risk_params.get('current_positions', 0)}
"""

    news_str = "\n".join(
        f"- [{n.get('sentiment', 'neutral')}] {n.get('title', 'N/A')} "
        f"(affects: {', '.join(n.get('affected_symbols', []))})"
        for n in news_analyses[:10]
    )

    return f"""You are an AI trading strategist for Indian equity markets.

Generate trade ideas based on the following information.

PORTFOLIO:
- Total value: ₹{portfolio_summary.get('total_value', 0):,.2f}
- Cash available: ₹{portfolio_summary.get('cash_balance', 0):,.2f}
- Current P&L: ₹{portfolio_summary.get('total_pnl', 0):,.2f}
- Open positions: {portfolio_summary.get('positions_count', 0)}
{risk_str}

RECENT NEWS ANALYSES:
{news_str if news_str else "No recent news available"}

MARKET CONTEXT:
{market_context or "Normal market conditions"}

Respond with ONLY valid JSON array of trade ideas:
[
    {{
        "symbol": "SYMBOL",
        "side": "BUY|SELL",
        "reason": "<clear trading rationale>",
        "confidence": <float 0-100>,
        "suggested_entry": <price>,
        "stop_loss": <price>,
        "take_profit": <price>,
        "position_size_pct": <float 1-10>,
        "risk_reward_ratio": <float>,
        "time_horizon": "intraday|1-3 days|1-2 weeks",
        "news_catalysts": ["catalyst1", "catalyst2"],
        "sector": "IT|Banking|Pharma|Auto|FMCG|Energy|Metals|Telecom"
    }}
]

Rules:
- Maximum 3 ideas per response
- Only suggest trades with risk:reward ratio ≥ 2:1
- Confidence must be realistic (most trades are 60-80%)
- Stop loss should be ~3-5% below entry for buys
- Take profit should be ~6-15% above entry for buys
- Consider current portfolio exposure to avoid concentration
- Prefer liquid NIFTY 50 / NIFTY Next 50 stocks
- No penny stocks or illiquid names"""


def morning_analysis_prompt(
    date: str,
    news_items: list[dict],
    portfolio_positions: list[dict],
    previous_day_summary: dict | None = None,
) -> str:
    """
    Prompt for the comprehensive morning analysis routine.
    """
    positions_str = "\n".join(
        f"- {p.get('symbol', 'N/A')}: {p.get('quantity', 0)} shares "
        f"@ ₹{p.get('average_price', 0):.2f} "
        f"(P&L: ₹{p.get('pnl', 0):,.2f})"
        for p in portfolio_positions
    ) if portfolio_positions else "No open positions"

    news_str = "\n".join(
        f"- [{n.get('source', 'Unknown')}] {n.get('title', 'N/A')}"
        for n in news_items[:20]
    )

    prev_str = ""
    if previous_day_summary:
        prev_str = f"""
PREVIOUS DAY:
- P&L: ₹{previous_day_summary.get('total_pnl', 0):,.2f}
- Trades: {previous_day_summary.get('trades_executed', 0)}
- Win rate: {previous_day_summary.get('win_rate', 0):.1f}%
"""

    return f"""You are a senior portfolio manager preparing the daily morning briefing for {date}.

Analyze all available information and provide a comprehensive market assessment.

CURRENT POSITIONS:
{positions_str}
{prev_str}

TODAY'S NEWS ({len(news_items)} items):
{news_str}

Respond with ONLY valid JSON:
{{
    "market_outlook": "bullish|neutral|bearish",
    "outlook_confidence": <float 0-100>,
    "key_events": [
        {{
            "event": "<description>",
            "impact": "high|medium|low",
            "affected_symbols": ["SYM1"],
            "recommendation": "<action>"
        }}
    ],
    "portfolio_actions": [
        {{
            "symbol": "SYMBOL",
            "action": "hold|add|reduce|exit",
            "reason": "<rationale>"
        }}
    ],
    "watchlist_additions": ["SYMBOL1", "SYMBOL2"],
    "risk_alerts": ["<alert message>"],
    "summary": "<2-3 sentence market summary>"
}}"""


def risk_assessment_prompt(
    trade_symbol: str,
    trade_side: str,
    trade_price: float,
    portfolio_positions: list[dict],
    recent_performance: dict,
) -> str:
    """
    Prompt for AI-powered risk assessment of a specific trade.
    """
    return f"""You are a risk management officer reviewing a proposed trade.

PROPOSED TRADE:
- Symbol: {trade_symbol}
- Side: {trade_side}
- Price: ₹{trade_price:.2f}

CURRENT PORTFOLIO:
{len(portfolio_positions)} open positions

RECENT PERFORMANCE:
- Win rate: {recent_performance.get('win_rate', 0):.1f}%
- Total P&L: ₹{recent_performance.get('total_pnl', 0):,.2f}
- Max drawdown: {recent_performance.get('max_drawdown', 0):.1f}%

Respond with ONLY valid JSON:
{{
    "risk_score": <float 0-100, higher = more risky>,
    "recommendation": "approve|caution|reject",
    "concerns": ["<concern 1>", "<concern 2>"],
    "suggested_stop_loss_pct": <float>,
    "suggested_position_size_pct": <float>,
    "reasoning": "<brief risk assessment>"
}}"""
