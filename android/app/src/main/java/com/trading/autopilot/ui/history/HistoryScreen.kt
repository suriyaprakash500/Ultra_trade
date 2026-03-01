package com.trading.autopilot.ui.history

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
import com.trading.autopilot.ui.components.*
import com.trading.autopilot.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HistoryScreen(
    viewModel: HistoryViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Trade History", fontWeight = FontWeight.Bold) },
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
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(10.dp),
            contentPadding = PaddingValues(vertical = 12.dp)
        ) {
            // ── Performance Summary ───────────────────────────
            item {
                GlassCard {
                    Text("Performance Summary", color = TextMuted, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        StatItem(
                            "Total P&L",
                            "₹${String.format("%,.2f", state.metrics.total_pnl)}",
                            valueColor = if (state.metrics.total_pnl >= 0) BullishGreen else BearishRed
                        )
                        StatItem(
                            "Win Rate",
                            "${String.format("%.1f", state.metrics.win_rate)}%",
                            valueColor = if (state.metrics.win_rate >= 50) BullishGreen else HotCoral
                        )
                        StatItem("Total", "${state.metrics.total_trades}")
                    }
                    Spacer(modifier = Modifier.height(8.dp))
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceEvenly
                    ) {
                        StatItem(
                            "Avg Win",
                            "₹${String.format("%.2f", state.metrics.avg_win)}",
                            valueColor = BullishGreen
                        )
                        StatItem(
                            "Avg Loss",
                            "₹${String.format("%.2f", state.metrics.avg_loss)}",
                            valueColor = BearishRed
                        )
                        StatItem(
                            "Max DD",
                            "${String.format("%.1f", state.metrics.max_drawdown)}%",
                            valueColor = if (state.metrics.max_drawdown > 10) HotCoral else TextPrimary
                        )
                    }
                }
            }

            // ── Trades ────────────────────────────────────────
            if (state.trades.isEmpty() && !state.isLoading) {
                item {
                    GlassCard {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text("📊", fontSize = 40.sp)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text("No trades yet", color = TextPrimary, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
                            Text("Trades will appear here once executed", color = TextMuted, fontSize = 13.sp)
                        }
                    }
                }
            }

            item { SectionHeader(title = "Completed Trades (${state.trades.size})") }

            items(state.trades) { trade ->
                GlassCard {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column(modifier = Modifier.weight(1f)) {
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                val sideColor = if (trade.side == "BUY") BullishGreen else BearishRed
                                Surface(
                                    shape = RoundedCornerShape(4.dp),
                                    color = sideColor.copy(alpha = 0.15f)
                                ) {
                                    Text(
                                        trade.side,
                                        color = sideColor,
                                        fontSize = 10.sp,
                                        fontWeight = FontWeight.Bold,
                                        modifier = Modifier.padding(horizontal = 6.dp, vertical = 2.dp)
                                    )
                                }
                                Spacer(modifier = Modifier.width(6.dp))
                                Text(trade.symbol, color = TextPrimary, fontWeight = FontWeight.SemiBold)
                                Spacer(modifier = Modifier.width(4.dp))
                                Text("${trade.quantity}x", color = TextMuted, fontSize = 12.sp)
                            }
                            Text(
                                "₹${String.format("%.2f", trade.entry_price)} → ₹${String.format("%.2f", trade.exit_price)}",
                                color = TextMuted,
                                fontSize = 12.sp
                            )
                            if (trade.reason.isNotEmpty()) {
                                Text(trade.reason, color = TextMuted, fontSize = 11.sp, maxLines = 1)
                            }
                        }
                        Column(horizontalAlignment = Alignment.End) {
                            PnlText(value = trade.pnl, fontSize = 15)
                            PnlText(value = trade.pnl_pct, prefix = "", suffix = "%", fontSize = 11)
                        }
                    }
                }
            }

            item { Spacer(modifier = Modifier.height(80.dp)) }
        }
    }
}
