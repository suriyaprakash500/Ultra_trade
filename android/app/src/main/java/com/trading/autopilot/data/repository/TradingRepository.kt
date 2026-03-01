package com.trading.autopilot.data.repository

import com.trading.autopilot.data.api.TradingApiService
import com.trading.autopilot.data.model.*
import javax.inject.Inject
import javax.inject.Singleton

/**
 * Single source of truth for all trading data.
 * Abstracts the API calls and handles errors gracefully.
 */
@Singleton
class TradingRepository @Inject constructor(
    private val api: TradingApiService
) {
    // ── Dashboard ────────────────────────────────────────────────
    suspend fun getDashboard(): Result<DashboardResponse> = runCatching {
        api.getDashboard()
    }

    // ── Portfolio ────────────────────────────────────────────────
    suspend fun getPortfolio(): Result<PortfolioResponse> = runCatching {
        api.getPortfolio()
    }

    suspend fun getPositions(): Result<List<PositionResponse>> = runCatching {
        api.getPositions()
    }

    suspend fun getMetrics(): Result<MetricsResponse> = runCatching {
        api.getMetrics()
    }

    // ── Trading ──────────────────────────────────────────────────
    suspend fun placeOrder(order: OrderRequest): Result<Map<String, Any>> = runCatching {
        api.placeOrder(order)
    }

    suspend fun cancelOrder(orderId: String): Result<Map<String, Any>> = runCatching {
        api.cancelOrder(orderId)
    }

    // ── AI & News ────────────────────────────────────────────────
    suspend fun getNews(): Result<List<NewsAnalysis>> = runCatching {
        api.getNews()
    }

    suspend fun runMorningRoutine(): Result<MorningBriefingResponse> = runCatching {
        api.runMorningRoutine()
    }

    suspend fun getTradeIdeas(): Result<List<TradeIdea>> = runCatching {
        api.getTradeIdeas()
    }

    suspend fun getMorningBriefing(): Result<MorningBriefingResponse> = runCatching {
        api.getMorningBriefing()
    }

    // ── Risk ─────────────────────────────────────────────────────
    suspend fun activateKillSwitch(reason: String): Result<KillSwitchResponse> = runCatching {
        api.activateKillSwitch(reason)
    }

    suspend fun deactivateKillSwitch(): Result<Map<String, Any>> = runCatching {
        api.deactivateKillSwitch()
    }

    suspend fun getKillSwitchStatus(): Result<KillSwitchStatus> = runCatching {
        api.getKillSwitchStatus()
    }

    // ── Market ───────────────────────────────────────────────────
    suspend fun getStockPrice(symbol: String): Result<StockPriceResponse> = runCatching {
        api.getStockPrice(symbol)
    }

    // ── Trades History ───────────────────────────────────────────
    suspend fun getTrades(): Result<List<TradeResponse>> = runCatching {
        api.getTrades()
    }

    // ── Health ───────────────────────────────────────────────────
    suspend fun getHealth(): Result<HealthResponse> = runCatching {
        api.getHealth()
    }
}
