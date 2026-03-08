"""
Trading Autopilot — MCP-Compatible Tool Server.

Implements an MCP-compatible tool server using Grok's OpenAI function calling.
Since fastmcp requires Python 3.10+ and we have 3.9, we implement the tool
registry and Grok function calling integration directly.

This approach is actually cleaner: Grok calls our tools as OpenAI-compatible
functions, and we expose them via a REST API for the Android app to trigger.
"""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List, Optional

from loguru import logger
from openai import OpenAI

from backend.config import get_settings


class ToolRegistry:
    """
    Registry of tools that can be called by Grok AI via function calling.

    Each tool is registered with:
    - A name
    - A description
    - A JSON schema for parameters
    - An async handler function
    """

    def __init__(self) -> None:
        self._tools: Dict[str, dict] = {}
        self._handlers: Dict[str, Callable] = {}

    def register(
        self,
        name: str,
        description: str,
        parameters: dict,
        handler: Callable,
    ) -> None:
        """Register a tool for Grok function calling."""
        self._tools[name] = {
            "type": "function",
            "function": {
                "name": name,
                "description": description,
                "parameters": parameters,
            },
        }
        self._handlers[name] = handler
        logger.debug(f"Tool registered: {name}")

    def get_tool_definitions(self) -> List[dict]:
        """Return all tool definitions in OpenAI function calling format."""
        return list(self._tools.values())

    def get_tool_names(self) -> List[str]:
        """Return all registered tool names."""
        return list(self._tools.keys())

    async def execute_tool(self, name: str, arguments: dict) -> Any:
        """
        Execute a registered tool by name with given arguments.

        Raises:
            KeyError: If the tool name is not registered.
        """
        if name not in self._handlers:
            raise KeyError(f"Tool '{name}' not found")

        handler = self._handlers[name]
        logger.info(f"Executing tool: {name}({arguments})")

        result = await handler(**arguments)

        logger.info(f"Tool {name} completed")
        return result


class GrokToolAgent:
    """
    Agent that uses Grok AI with function calling to interact
    with registered trading tools.

    This is the MCP-equivalent: Grok discovers available tools,
    decides which to call based on user/system prompts, and
    processes the results.
    """

    def __init__(self, registry: ToolRegistry) -> None:
        self._settings = get_settings()
        self._registry = registry
        self._client: Optional[OpenAI] = None
        self._conversation_history: List[dict] = []

    def _get_client(self) -> OpenAI:
        """Lazy-initialize the Grok API client."""
        if self._client is None:
            self._client = OpenAI(
                api_key=self._settings.grok_api_key,
                base_url=self._settings.grok_base_url,
            )
        return self._client

    async def chat(
        self,
        user_message: str,
        system_prompt: str = "",
        max_tool_calls: int = 5,
    ) -> dict:
        """
        Send a message to Grok with access to all registered tools.

        Grok will decide which tools to call (if any) and return
        a final response after processing tool results.

        Args:
            user_message: The user's query or instruction.
            system_prompt: Optional system-level context.
            max_tool_calls: Maximum number of tool calls per turn.

        Returns:
            dict with 'response' (text) and 'tool_calls' (list of calls made).
        """
        if not system_prompt:
            system_prompt = (
                "You are an AI trading assistant for Indian equity markets (NSE/BSE). "
                "You have access to trading tools for portfolio management, "
                "market data, news analysis, and order execution. "
                "The system is in PAPER TRADING mode — no real money is at risk. "
                "Always check risk before placing trades. "
                "Be concise and actionable in your responses."
            )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]

        tools = self._registry.get_tool_definitions()
        tool_calls_made: List[dict] = []

        try:
            client = self._get_client()

            for iteration in range(max_tool_calls):
                response = client.chat.completions.create(
                    model=self._settings.grok_model,
                    messages=messages,
                    tools=tools if tools else None,
                    tool_choice="auto" if tools else None,
                    temperature=0.3,
                )

                message = response.choices[0].message

                # If Grok wants to call tools
                if message.tool_calls:
                    messages.append(message.model_dump())

                    for tool_call in message.tool_calls:
                        func_name = tool_call.function.name
                        func_args = json.loads(tool_call.function.arguments)

                        logger.info(
                            f"Grok calling tool: {func_name}({func_args})"
                        )

                        try:
                            result = await self._registry.execute_tool(
                                func_name, func_args
                            )
                            result_str = json.dumps(result, default=str)
                        except Exception as exc:
                            result_str = json.dumps({"error": str(exc)})
                            logger.error(f"Tool {func_name} failed: {exc}")

                        tool_calls_made.append({
                            "tool": func_name,
                            "arguments": func_args,
                            "result": result_str[:1000],  # Truncate for logging
                        })

                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result_str,
                        })
                else:
                    # No more tool calls — return final response
                    return {
                        "response": message.content or "",
                        "tool_calls": tool_calls_made,
                        "iterations": iteration + 1,
                    }

            # Max iterations reached
            return {
                "response": "Maximum tool calls reached. Please refine your request.",
                "tool_calls": tool_calls_made,
                "iterations": max_tool_calls,
            }

        except Exception as exc:
            logger.error(f"Grok agent error: {exc}")
            return {
                "response": f"Error communicating with AI: {exc}",
                "tool_calls": tool_calls_made,
                "iterations": 0,
            }


def create_tool_registry() -> ToolRegistry:
    """
    Create and populate the tool registry with all trading tools.

    Returns a ToolRegistry with all tools registered and ready for Grok.
    """
    registry = ToolRegistry()

    # ═══ Trading Tools ═══════════════════════════════════════════

    async def _place_order(
        symbol: str,
        side: str,
        quantity: int,
        order_type: str = "MARKET",
        price: float = 0.0,
        stop_loss: float = 0.0,
        take_profit: float = 0.0,
        reason: str = "",
    ) -> dict:
        from backend.data.models import OrderCreate, OrderSide, OrderType
        from backend.trading.order_manager import get_order_manager

        order = OrderCreate(
            symbol=symbol.upper(),
            side=OrderSide(side.upper()),
            order_type=OrderType(order_type.upper()),
            quantity=quantity,
            price=price,
            reason=reason,
            stop_loss=stop_loss if stop_loss > 0 else None,
            take_profit=take_profit if take_profit > 0 else None,
        )
        manager = get_order_manager()
        return await manager.submit_order(
            order=order,
            current_market_price=price if price > 0 else None,
        )

    registry.register(
        name="place_order",
        description="Place a buy or sell order for a stock. The system is in paper trading mode.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol (e.g. RELIANCE, TCS)"},
                "side": {"type": "string", "enum": ["BUY", "SELL"], "description": "Buy or sell"},
                "quantity": {"type": "integer", "description": "Number of shares"},
                "order_type": {"type": "string", "enum": ["MARKET", "LIMIT"], "default": "MARKET"},
                "price": {"type": "number", "description": "Price for limit orders", "default": 0},
                "stop_loss": {"type": "number", "description": "Stop loss price", "default": 0},
                "take_profit": {"type": "number", "description": "Take profit target", "default": 0},
                "reason": {"type": "string", "description": "Reason for the trade"},
            },
            "required": ["symbol", "side", "quantity"],
        },
        handler=_place_order,
    )

    # ═══ Portfolio Tools ═════════════════════════════════════════

    async def _get_portfolio() -> dict:
        from backend.trading.portfolio_tracker import get_portfolio_tracker
        return get_portfolio_tracker().get_current_portfolio()

    registry.register(
        name="get_portfolio",
        description="Get current portfolio summary: total value, cash, P&L, positions count.",
        parameters={"type": "object", "properties": {}},
        handler=_get_portfolio,
    )

    async def _get_positions() -> list:
        from backend.trading.portfolio_tracker import get_portfolio_tracker
        return get_portfolio_tracker().get_positions()

    registry.register(
        name="get_positions",
        description="Get all open positions with symbol, quantity, price, and P&L.",
        parameters={"type": "object", "properties": {}},
        handler=_get_positions,
    )

    async def _get_performance() -> dict:
        from backend.trading.portfolio_tracker import get_portfolio_tracker
        return get_portfolio_tracker().get_performance_metrics()

    registry.register(
        name="get_performance_metrics",
        description="Get trading performance: win rate, profit factor, Sharpe ratio, max drawdown.",
        parameters={"type": "object", "properties": {}},
        handler=_get_performance,
    )

    # ═══ Market Data Tools ═══════════════════════════════════════

    async def _get_stock_price(symbol: str) -> dict:
        from backend.mcp_server.tools.market_tools import fetch_stock_price
        return await fetch_stock_price(symbol)

    registry.register(
        name="get_stock_price",
        description="Get current market price, day high/low, volume, PE ratio for an NSE stock.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol (e.g. RELIANCE)"},
            },
            "required": ["symbol"],
        },
        handler=_get_stock_price,
    )

    async def _get_stock_history(symbol: str, period: str = "1mo") -> dict:
        from backend.mcp_server.tools.market_tools import fetch_stock_history
        return await fetch_stock_history(symbol, period)

    registry.register(
        name="get_stock_history",
        description="Get historical OHLCV data and volatility for a stock.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol"},
                "period": {
                    "type": "string",
                    "enum": ["1d", "5d", "1mo", "3mo", "6mo", "1y"],
                    "default": "1mo",
                },
            },
            "required": ["symbol"],
        },
        handler=_get_stock_history,
    )

    # ═══ Analysis Tools ══════════════════════════════════════════

    async def _analyze_news() -> list:
        from backend.ai.news_analyzer import get_news_analyzer
        analyzer = get_news_analyzer()
        raw = await analyzer.fetch_all_news(max_per_source=5)
        return await analyzer.analyze_batch(raw, max_items=5)

    registry.register(
        name="analyze_news",
        description="Fetch latest Indian financial news and analyze sentiment using AI.",
        parameters={"type": "object", "properties": {}},
        handler=_analyze_news,
    )

    async def _check_risk(
        symbol: str, side: str, price: float,
        ai_confidence: float = 75.0,
    ) -> dict:
        from backend.risk.safety_layers import get_safety_layers, TradeProposal
        from backend.risk.correlation import get_sector

        proposal = TradeProposal(
            symbol=symbol.upper(),
            side=side.upper(),
            quantity=1,
            price=price,
            sector=get_sector(symbol),
            ai_confidence=ai_confidence,
            news_sources=1,
        )
        safety = get_safety_layers()
        result = safety.check_all(proposal)
        return result.model_dump()

    registry.register(
        name="check_trade_risk",
        description="Check if a proposed trade passes the 7-layer safety system.",
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "Stock symbol"},
                "side": {"type": "string", "enum": ["BUY", "SELL"]},
                "price": {"type": "number", "description": "Trade price"},
                "ai_confidence": {"type": "number", "default": 75},
            },
            "required": ["symbol", "side", "price"],
        },
        handler=_check_risk,
    )

    # ═══ Kill Switch ═════════════════════════════════════════════

    async def _kill_switch(reason: str = "Manual trigger") -> dict:
        from backend.risk.kill_switch import get_kill_switch
        ks = get_kill_switch()
        return await ks.activate(reason=reason)

    registry.register(
        name="activate_kill_switch",
        description="EMERGENCY: Close all positions and halt all trading immediately.",
        parameters={
            "type": "object",
            "properties": {
                "reason": {"type": "string", "default": "Manual trigger"},
            },
        },
        handler=_kill_switch,
    )

    # ═══ Technical Analysis Tool ═════════════════════════════════

    async def _get_technical(symbol: str) -> dict:
        from backend.mcp_server.tools.market_tools import fetch_technical_indicators
        return await fetch_technical_indicators(symbol)

    registry.register(
        name="get_technical_indicators",
        description=(
            "Get technical analysis for a stock: RSI, MACD, Bollinger Bands, "
            "moving averages (SMA 20/50/200, EMA 12/26), volume analysis, "
            "support/resistance levels, and overall signal."
        ),
        parameters={
            "type": "object",
            "properties": {
                "symbol": {"type": "string", "description": "NSE stock symbol (e.g. RELIANCE)"},
            },
            "required": ["symbol"],
        },
        handler=_get_technical,
    )

    logger.info(f"Tool registry created with {len(registry.get_tool_names())} tools")
    return registry


# ── Module-level singletons ───────────────────────────────────────

_registry: Optional[ToolRegistry] = None
_agent: Optional[GrokToolAgent] = None


def get_tool_registry() -> ToolRegistry:
    """Return the global ToolRegistry singleton."""
    global _registry
    if _registry is None:
        _registry = create_tool_registry()
    return _registry


def get_grok_agent() -> GrokToolAgent:
    """Return the global GrokToolAgent singleton."""
    global _agent
    if _agent is None:
        _agent = GrokToolAgent(get_tool_registry())
    return _agent
