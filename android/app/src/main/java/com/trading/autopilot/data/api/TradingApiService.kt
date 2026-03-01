package com.trading.autopilot.data.api

import com.trading.autopilot.data.model.*
import retrofit2.http.*

/**
 * Retrofit service interface matching the Python backend REST API.
 * All endpoints (except health) require X-API-Key header.
 */
interface TradingApiService {

    // ── Health ────────────────────────────────────────────────────
    @GET("health")
    suspend fun getHealth(): HealthResponse

    // ── Dashboard ────────────────────────────────────────────────
    @GET("api/dashboard")
    suspend fun getDashboard(): DashboardResponse

    // ── Portfolio ────────────────────────────────────────────────
    @GET("api/portfolio")
    suspend fun getPortfolio(): PortfolioResponse

    @GET("api/positions")
    suspend fun getPositions(): List<PositionResponse>

    @GET("api/trades")
    suspend fun getTrades(): List<TradeResponse>

    @GET("api/metrics")
    suspend fun getMetrics(): MetricsResponse

    // ── Trading ──────────────────────────────────────────────────
    @POST("api/orders")
    suspend fun placeOrder(@Body order: OrderRequest): Map<String, Any>

    @DELETE("api/orders/{orderId}")
    suspend fun cancelOrder(@Path("orderId") orderId: String): Map<String, Any>

    // ── Market Data ──────────────────────────────────────────────
    @GET("api/market/price/{symbol}")
    suspend fun getStockPrice(@Path("symbol") symbol: String): StockPriceResponse

    // ── AI & News ────────────────────────────────────────────────
    @GET("api/news")
    suspend fun getNews(): List<NewsAnalysis>

    @POST("api/ai/morning-routine")
    suspend fun runMorningRoutine(): MorningBriefingResponse

    @GET("api/ai/trade-ideas")
    suspend fun getTradeIdeas(): List<TradeIdea>

    @GET("api/ai/morning-briefing")
    suspend fun getMorningBriefing(): MorningBriefingResponse

    // ── Risk ─────────────────────────────────────────────────────
    @POST("api/risk/kill-switch/activate")
    suspend fun activateKillSwitch(
        @Query("reason") reason: String = "Manual activation from app"
    ): KillSwitchResponse

    @POST("api/risk/kill-switch/deactivate")
    suspend fun deactivateKillSwitch(): Map<String, Any>

    @GET("api/risk/kill-switch/status")
    suspend fun getKillSwitchStatus(): KillSwitchStatus

    // ── Kite Auth ────────────────────────────────────────────────
    @GET("api/kite/login-url")
    suspend fun getKiteLoginUrl(): Map<String, String>

    @GET("api/kite/status")
    suspend fun getKiteStatus(): Map<String, Any>
}
