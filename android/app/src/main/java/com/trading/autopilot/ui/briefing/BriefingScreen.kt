package com.trading.autopilot.ui.briefing

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.WbSunny
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
fun BriefingScreen(
    viewModel: BriefingViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Morning Briefing", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepNavy)
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { viewModel.runMorningRoutine() },
                containerColor = ElectricCyan,
                contentColor = DeepNavy,
                shape = RoundedCornerShape(16.dp)
            ) {
                if (state.isRunning) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = DeepNavy,
                        strokeWidth = 2.dp
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Running...", fontWeight = FontWeight.Bold)
                } else {
                    Icon(Icons.Default.WbSunny, "Run")
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Run Morning Routine", fontWeight = FontWeight.Bold)
                }
            }
        },
        containerColor = DeepNavy
    ) { padding ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(horizontal = 16.dp),
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(vertical = 12.dp)
        ) {
            state.error?.let { error ->
                item {
                    GlassCard {
                        Text("⚠️ $error", color = HotCoral, fontSize = 13.sp)
                    }
                }
            }

            val briefing = state.briefing
            if (briefing == null) {
                item {
                    GlassCard {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text("☀️", fontSize = 40.sp)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                "No morning briefing yet",
                                color = TextPrimary,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                            Text(
                                "Tap 'Run Morning Routine' to fetch news,\nanalyze markets, and get AI insights",
                                color = TextMuted,
                                fontSize = 13.sp
                            )
                        }
                    }
                }
            } else {
                val mb = briefing.morning_briefing

                // ── Market Outlook ────────────────────────────
                item {
                    GlassCard {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.CenterVertically
                        ) {
                            Column {
                                Text("Market Outlook", color = TextMuted, fontSize = 12.sp)
                                val outlookEmoji = when (mb.market_outlook.lowercase()) {
                                    "bullish" -> "🟢 BULLISH"
                                    "bearish" -> "🔴 BEARISH"
                                    else -> "⚪ NEUTRAL"
                                }
                                Text(
                                    outlookEmoji,
                                    fontSize = 20.sp,
                                    fontWeight = FontWeight.Bold,
                                    color = when (mb.market_outlook.lowercase()) {
                                        "bullish" -> BullishGreen
                                        "bearish" -> BearishRed
                                        else -> TextSecondary
                                    }
                                )
                            }
                            ConfidenceBar(
                                mb.outlook_confidence,
                                modifier = Modifier.width(120.dp)
                            )
                        }

                        if (mb.summary.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(mb.summary, color = TextSecondary, fontSize = 13.sp)
                        }
                    }
                }

                // ── Stats ─────────────────────────────────────
                item {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.spacedBy(8.dp)
                    ) {
                        GlassCard(modifier = Modifier.weight(1f)) {
                            Text("News", color = TextMuted, fontSize = 11.sp)
                            Text("${briefing.news_analyzed}", color = ElectricCyan, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                        }
                        GlassCard(modifier = Modifier.weight(1f)) {
                            Text("Ideas", color = TextMuted, fontSize = 11.sp)
                            Text("${briefing.trade_ideas.size}", color = NeonGreen, fontSize = 20.sp, fontWeight = FontWeight.Bold)
                        }
                    }
                }

                // ── Key Events ────────────────────────────────
                if (mb.key_events.isNotEmpty()) {
                    item { SectionHeader(title = "Key Events") }
                    items(mb.key_events) { event ->
                        GlassCard {
                            Text(event.event, color = TextPrimary, fontSize = 14.sp, fontWeight = FontWeight.Medium)
                            Row {
                                SentimentBadge(event.impact)
                                if (event.affected_symbols.isNotEmpty()) {
                                    Spacer(modifier = Modifier.width(8.dp))
                                    Text(
                                        event.affected_symbols.joinToString(", "),
                                        color = ElectricCyan,
                                        fontSize = 11.sp
                                    )
                                }
                            }
                            if (event.recommendation.isNotEmpty()) {
                                Text(event.recommendation, color = TextMuted, fontSize = 12.sp)
                            }
                        }
                    }
                }

                // ── Risk Alerts ───────────────────────────────
                if (mb.risk_alerts.isNotEmpty()) {
                    item { SectionHeader(title = "⚠️ Risk Alerts") }
                    items(mb.risk_alerts) { alert ->
                        GlassCard {
                            Text(alert, color = AmberWarning, fontSize = 13.sp)
                        }
                    }
                }

                // ── Trade Ideas from briefing ─────────────────
                if (briefing.trade_ideas.isNotEmpty()) {
                    item { SectionHeader(title = "Suggested Trades") }
                    items(briefing.trade_ideas) { idea ->
                        GlassCard {
                            Row(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalArrangement = Arrangement.SpaceBetween
                            ) {
                                Column {
                                    Row(verticalAlignment = Alignment.CenterVertically) {
                                        val sideColor = if (idea.side == "BUY") BullishGreen else BearishRed
                                        Text(idea.side, color = sideColor, fontWeight = FontWeight.Bold, fontSize = 12.sp)
                                        Spacer(modifier = Modifier.width(6.dp))
                                        Text(idea.symbol, color = TextPrimary, fontWeight = FontWeight.SemiBold)
                                    }
                                    Text(idea.reason, color = TextMuted, fontSize = 12.sp)
                                }
                                Column(horizontalAlignment = Alignment.End) {
                                    Text("${idea.confidence.toInt()}%", color = ElectricCyan, fontWeight = FontWeight.Bold)
                                }
                            }
                        }
                    }
                }
            }

            item { Spacer(modifier = Modifier.height(80.dp)) }
        }
    }
}
