package com.trading.autopilot.ui.dashboard

import androidx.compose.foundation.background
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Refresh
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.trading.autopilot.data.model.PositionResponse
import com.trading.autopilot.ui.components.*
import com.trading.autopilot.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun DashboardScreen(
    viewModel: DashboardViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Column {
                        Text("Trading Autopilot", fontSize = 18.sp, fontWeight = FontWeight.Bold)
                        Text(
                            "PAPER MODE",
                            fontSize = 10.sp,
                            color = AmberWarning,
                            fontWeight = FontWeight.SemiBold
                        )
                    }
                },
                actions = {
                    IconButton(onClick = { viewModel.refresh() }) {
                        Icon(Icons.Default.Refresh, "Refresh", tint = ElectricCyan)
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepNavy)
            )
        },
        containerColor = DeepNavy
    ) { padding ->
        if (state.isLoading && state.portfolio.total_value == 0.0) {
            Box(
                modifier = Modifier.fillMaxSize().padding(padding),
                contentAlignment = Alignment.Center
            ) {
                CircularProgressIndicator(color = ElectricCyan)
            }
        } else {
            LazyColumn(
                modifier = Modifier
                    .fillMaxSize()
                    .padding(padding)
                    .padding(horizontal = 16.dp),
                verticalArrangement = Arrangement.spacedBy(12.dp),
                contentPadding = PaddingValues(vertical = 12.dp)
            ) {
                // Error banner
                state.error?.let { error ->
                    item {
                        GlassCard {
                            Text("⚠️ $error", color = HotCoral, fontSize = 13.sp)
                        }
                    }
                }

                // ── Portfolio Card ─────────────────────────────
                item { PortfolioCard(state) }

                // ── Quick Metrics ──────────────────────────────
                item { MetricsRow(state) }

                // ── Kill Switch ────────────────────────────────
                item {
                    KillSwitchButton(
                        isActive = state.killSwitchActive,
                        isLoading = state.killSwitchLoading,
                        onClick = { viewModel.toggleKillSwitch() }
                    )
                }

                // ── Positions ──────────────────────────────────
                if (state.positions.isNotEmpty()) {
                    item {
                        SectionHeader(
                            title = "Open Positions (${state.positions.size})"
                        )
                    }
                    items(state.positions) { position ->
                        PositionCard(position)
                    }
                } else {
                    item {
                        GlassCard {
                            Text(
                                "No open positions",
                                color = TextMuted,
                                fontSize = 14.sp,
                                modifier = Modifier.fillMaxWidth()
                            )
                        }
                    }
                }

                // ── Recent Trades ──────────────────────────────
                if (state.recentTrades.isNotEmpty()) {
                    item { SectionHeader(title = "Recent Trades") }
                    items(state.recentTrades.take(5)) { trade ->
                        GlassCard {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Column {
                                    Text(trade.symbol, color = TextPrimary, fontWeight = FontWeight.SemiBold)
                                    Text(
                                        "${trade.side} ${trade.quantity}x",
                                        color = TextMuted,
                                        fontSize = 12.sp
                                    )
                                }
                                PnlText(value = trade.pnl, fontSize = 15)
                            }
                        }
                    }
                }

                item { Spacer(modifier = Modifier.height(80.dp)) }
            }
        }
    }
}

@Composable
private fun PortfolioCard(state: DashboardUiState) {
    GlassCard {
        Text("Portfolio Value", color = TextMuted, fontSize = 12.sp, fontWeight = FontWeight.Medium)
        Spacer(modifier = Modifier.height(4.dp))
        Text(
            "₹${String.format("%,.2f", state.portfolio.total_value)}",
            color = TextPrimary,
            fontSize = 28.sp,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(8.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween
        ) {
            Column {
                Text("Today's P&L", color = TextMuted, fontSize = 11.sp)
                PnlText(value = state.portfolio.total_pnl, fontSize = 16)
            }
            Column(horizontalAlignment = Alignment.End) {
                Text("Return", color = TextMuted, fontSize = 11.sp)
                PnlText(value = state.portfolio.total_pnl_pct, prefix = "", suffix = "%", fontSize = 16)
            }
        }

        Spacer(modifier = Modifier.height(12.dp))
        HorizontalDivider(color = CardBorder)
        Spacer(modifier = Modifier.height(12.dp))

        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            StatItem("Cash", "₹${String.format("%,.0f", state.portfolio.cash_balance)}")
            StatItem("Invested", "₹${String.format("%,.0f", state.portfolio.invested_value)}")
            StatItem("Drawdown", "${String.format("%.1f", state.portfolio.drawdown)}%",
                valueColor = if (state.portfolio.drawdown > 5) HotCoral else TextPrimary
            )
        }
    }
}

@Composable
private fun MetricsRow(state: DashboardUiState) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.spacedBy(8.dp)
    ) {
        GlassCard(modifier = Modifier.weight(1f)) {
            Text("Win Rate", color = TextMuted, fontSize = 11.sp)
            Text(
                "${String.format("%.1f", state.metrics.win_rate)}%",
                color = if (state.metrics.win_rate >= 50) BullishGreen else HotCoral,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        }
        GlassCard(modifier = Modifier.weight(1f)) {
            Text("Trades", color = TextMuted, fontSize = 11.sp)
            Text(
                "${state.metrics.total_trades}",
                color = ElectricCyan,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        }
        GlassCard(modifier = Modifier.weight(1f)) {
            Text("Sharpe", color = TextMuted, fontSize = 11.sp)
            Text(
                String.format("%.2f", state.metrics.sharpe_ratio),
                color = TextPrimary,
                fontSize = 20.sp,
                fontWeight = FontWeight.Bold
            )
        }
    }
}

@Composable
private fun PositionCard(position: PositionResponse) {
    GlassCard {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Column(modifier = Modifier.weight(1f)) {
                Text(
                    position.symbol,
                    color = TextPrimary,
                    fontSize = 16.sp,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "${position.quantity} shares @ ₹${String.format("%.2f", position.average_price)}",
                    color = TextMuted,
                    fontSize = 12.sp
                )
                if (position.stop_loss > 0) {
                    Text(
                        "SL: ₹${String.format("%.2f", position.stop_loss)}",
                        color = HotCoral.copy(alpha = 0.7f),
                        fontSize = 11.sp
                    )
                }
            }
            Column(horizontalAlignment = Alignment.End) {
                PnlText(value = position.pnl, fontSize = 16)
                PnlText(
                    value = position.pnl_pct,
                    prefix = "",
                    suffix = "%",
                    fontSize = 12
                )
            }
        }
    }
}
