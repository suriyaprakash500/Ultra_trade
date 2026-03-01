package com.trading.autopilot.data.model

/**
 * API response data classes matching the Python backend schemas.
 */

// ── Health ────────────────────────────────────────────────────────
data class HealthResponse(
    val status: String = "",
    val trading_mode: String = "paper",
    val version: String = "",
    val uptime_seconds: Double = 0.0
)

// ── Portfolio ─────────────────────────────────────────────────────
data class PortfolioResponse(
    val total_value: Double = 0.0,
    val cash_balance: Double = 0.0,
    val invested_value: Double = 0.0,
    val market_value: Double = 0.0,
    val total_pnl: Double = 0.0,
    val total_pnl_pct: Double = 0.0,
    val positions_count: Int = 0,
    val drawdown: Double = 0.0,
    val starting_capital: Double = 0.0,
    val trading_mode: String = "paper"
)

// ── Position ──────────────────────────────────────────────────────
data class PositionResponse(
    val symbol: String = "",
    val exchange: String = "NSE",
    val quantity: Int = 0,
    val average_price: Double = 0.0,
    val current_price: Double = 0.0,
    val market_value: Double = 0.0,
    val pnl: Double = 0.0,
    val pnl_pct: Double = 0.0,
    val sector: String = "unknown",
    val stop_loss: Double = 0.0,
    val take_profit: Double = 0.0
)

// ── Dashboard ─────────────────────────────────────────────────────
data class DashboardResponse(
    val portfolio: PortfolioResponse = PortfolioResponse(),
    val positions: List<PositionResponse> = emptyList(),
    val recent_trades: List<TradeResponse> = emptyList(),
    val metrics: MetricsResponse = MetricsResponse(),
    val order_history: List<OrderResponse> = emptyList()
)

// ── Metrics ───────────────────────────────────────────────────────
data class MetricsResponse(
    val total_trades: Int = 0,
    val win_count: Int = 0,
    val loss_count: Int = 0,
    val win_rate: Double = 0.0,
    val total_pnl: Double = 0.0,
    val avg_win: Double = 0.0,
    val avg_loss: Double = 0.0,
    val profit_factor: Double = 0.0,
    val max_drawdown: Double = 0.0,
    val sharpe_ratio: Double = 0.0
)

// ── Trade ─────────────────────────────────────────────────────────
data class TradeResponse(
    val symbol: String = "",
    val side: String = "",
    val quantity: Int = 0,
    val entry_price: Double = 0.0,
    val exit_price: Double = 0.0,
    val pnl: Double = 0.0,
    val pnl_pct: Double = 0.0,
    val reason: String = "",
    val exited_at: String = ""
)

// ── Order ─────────────────────────────────────────────────────────
data class OrderResponse(
    val order_id: String = "",
    val symbol: String = "",
    val side: String = "",
    val order_type: String = "MARKET",
    val quantity: Int = 0,
    val price: Double = 0.0,
    val status: String = "",
    val executed_price: Double = 0.0,
    val reason: String = "",
    val created_at: String = ""
)

// ── Order Request ─────────────────────────────────────────────────
data class OrderRequest(
    val symbol: String,
    val side: String,
    val order_type: String = "MARKET",
    val quantity: Int,
    val price: Double = 0.0,
    val stop_loss: Double? = null,
    val take_profit: Double? = null,
    val reason: String = ""
)

// ── Trade Idea ────────────────────────────────────────────────────
data class TradeIdea(
    val symbol: String = "",
    val side: String = "BUY",
    val reason: String = "",
    val confidence: Double = 0.0,
    val suggested_entry: Double = 0.0,
    val stop_loss: Double = 0.0,
    val take_profit: Double = 0.0,
    val position_size_pct: Double = 0.0,
    val risk_reward_ratio: Double = 0.0,
    val time_horizon: String = "",
    val news_catalysts: List<String> = emptyList(),
    val sector: String = "",
    val status: String = "approved",
    val position_size: Int = 0,
    val kelly_fraction: Double = 0.0,
    val actual_risk: Double = 0.0,
    val risk_warnings: List<String> = emptyList()
)

// ── News ──────────────────────────────────────────────────────────
data class NewsAnalysis(
    val title: String = "",
    val sentiment: String = "neutral",
    val sentiment_score: Double = 0.0,
    val impact_level: String = "low",
    val affected_symbols: List<String> = emptyList(),
    val summary: String = "",
    val confidence: Double = 0.0,
    val recommended_action: String = "watch",
    val url: String = "",
    val original_source: String = ""
)

// ── Morning Briefing ──────────────────────────────────────────────
data class MorningBriefingResponse(
    val date: String = "",
    val run_at: String = "",
    val news_collected: Int = 0,
    val news_analyzed: Int = 0,
    val news_analyses: List<NewsAnalysis> = emptyList(),
    val portfolio_summary: PortfolioResponse = PortfolioResponse(),
    val positions: List<PositionResponse> = emptyList(),
    val morning_briefing: MorningBriefing = MorningBriefing(),
    val trade_ideas: List<TradeIdea> = emptyList(),
    val status: String = ""
)

data class MorningBriefing(
    val market_outlook: String = "neutral",
    val outlook_confidence: Double = 50.0,
    val key_events: List<KeyEvent> = emptyList(),
    val portfolio_actions: List<PortfolioAction> = emptyList(),
    val watchlist_additions: List<String> = emptyList(),
    val risk_alerts: List<String> = emptyList(),
    val summary: String = ""
)

data class KeyEvent(
    val event: String = "",
    val impact: String = "low",
    val affected_symbols: List<String> = emptyList(),
    val recommendation: String = ""
)

data class PortfolioAction(
    val symbol: String = "",
    val action: String = "hold",
    val reason: String = ""
)

// ── Kill Switch ───────────────────────────────────────────────────
data class KillSwitchStatus(
    val active: Boolean = false,
    val history: List<Map<String, Any>> = emptyList()
)

data class KillSwitchResponse(
    val activated_at: String = "",
    val reason: String = "",
    val positions_closed: Int = 0
)

// ── Risk Check ────────────────────────────────────────────────────
data class RiskCheckResponse(
    val passed: Boolean = false,
    val layers_checked: Int = 0,
    val layers_passed: Int = 0,
    val blocked_by: String? = null,
    val warnings: List<String> = emptyList()
)

// ── Stock Price ───────────────────────────────────────────────────
data class StockPriceResponse(
    val symbol: String = "",
    val current_price: Double = 0.0,
    val previous_close: Double = 0.0,
    val change: Double = 0.0,
    val change_pct: Double = 0.0,
    val day_high: Double = 0.0,
    val day_low: Double = 0.0,
    val volume: Long = 0,
    val sector: String = ""
)
