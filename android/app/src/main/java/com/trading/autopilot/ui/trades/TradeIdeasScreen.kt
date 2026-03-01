package com.trading.autopilot.ui.trades

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.AutoAwesome
import androidx.compose.material.icons.filled.Check
import androidx.compose.material.icons.filled.Close
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.trading.autopilot.data.model.TradeIdea
import com.trading.autopilot.ui.components.*
import com.trading.autopilot.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun TradeIdeasScreen(
    viewModel: TradeIdeasViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("AI Trade Ideas", fontWeight = FontWeight.Bold) },
                colors = TopAppBarDefaults.topAppBarColors(containerColor = DeepNavy)
            )
        },
        floatingActionButton = {
            ExtendedFloatingActionButton(
                onClick = { viewModel.generateIdeas() },
                containerColor = ElectricCyan,
                contentColor = DeepNavy,
                shape = RoundedCornerShape(16.dp)
            ) {
                if (state.isGenerating) {
                    CircularProgressIndicator(
                        modifier = Modifier.size(20.dp),
                        color = DeepNavy,
                        strokeWidth = 2.dp
                    )
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Generating...", fontWeight = FontWeight.Bold)
                } else {
                    Icon(Icons.Default.AutoAwesome, "Generate")
                    Spacer(modifier = Modifier.width(8.dp))
                    Text("Generate Ideas", fontWeight = FontWeight.Bold)
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

            state.successMessage?.let { message ->
                item {
                    GlassCard {
                        Text(message, color = BullishGreen, fontSize = 14.sp, fontWeight = FontWeight.SemiBold)
                    }
                }
            }

            if (state.ideas.isEmpty() && !state.isGenerating) {
                item {
                    GlassCard {
                        Column(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalAlignment = Alignment.CenterHorizontally
                        ) {
                            Text("🤖", fontSize = 40.sp)
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                "No trade ideas yet",
                                color = TextPrimary,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                            Text(
                                "Tap 'Generate Ideas' to have Grok AI analyze\nthe market and suggest trades",
                                color = TextMuted,
                                fontSize = 13.sp
                            )
                        }
                    }
                }
            }

            items(state.ideas) { idea ->
                TradeIdeaCard(
                    idea = idea,
                    onApprove = { viewModel.executeIdea(it) },
                    onReject = {}  // TODO: track rejections
                )
            }

            item { Spacer(modifier = Modifier.height(80.dp)) }
        }
    }
}

@Composable
private fun TradeIdeaCard(
    idea: TradeIdea,
    onApprove: (TradeIdea) -> Unit,
    onReject: (TradeIdea) -> Unit
) {
    val sideColor = if (idea.side == "BUY") BullishGreen else BearishRed

    GlassCard {
        // Header
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Surface(
                    shape = RoundedCornerShape(6.dp),
                    color = sideColor.copy(alpha = 0.15f)
                ) {
                    Text(
                        idea.side,
                        color = sideColor,
                        fontWeight = FontWeight.Bold,
                        fontSize = 12.sp,
                        modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
                    )
                }
                Spacer(modifier = Modifier.width(8.dp))
                Text(idea.symbol, color = TextPrimary, fontSize = 18.sp, fontWeight = FontWeight.Bold)
            }
            if (idea.sector.isNotEmpty()) {
                Text(idea.sector, color = TextMuted, fontSize = 11.sp)
            }
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Confidence bar
        ConfidenceBar(idea.confidence)

        Spacer(modifier = Modifier.height(8.dp))

        // Price details
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceEvenly
        ) {
            StatItem("Entry", "₹${String.format("%.2f", idea.suggested_entry)}", valueColor = ElectricCyan)
            StatItem("Stop Loss", "₹${String.format("%.2f", idea.stop_loss)}", valueColor = HotCoral)
            StatItem("Target", "₹${String.format("%.2f", idea.take_profit)}", valueColor = BullishGreen)
        }

        Spacer(modifier = Modifier.height(8.dp))

        // Reason
        Text(idea.reason, color = TextSecondary, fontSize = 13.sp)

        // Risk warnings
        idea.risk_warnings.forEach { warning ->
            Text("⚠️ $warning", color = AmberWarning, fontSize = 11.sp)
        }

        Spacer(modifier = Modifier.height(12.dp))

        // Action buttons
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            OutlinedButton(
                onClick = { onReject(idea) },
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.outlinedButtonColors(contentColor = HotCoral)
            ) {
                Icon(Icons.Default.Close, "Reject", modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(4.dp))
                Text("Skip")
            }
            Button(
                onClick = { onApprove(idea) },
                modifier = Modifier.weight(1f),
                shape = RoundedCornerShape(10.dp),
                colors = ButtonDefaults.buttonColors(containerColor = BullishGreen, contentColor = DeepNavy)
            ) {
                Icon(Icons.Default.Check, "Approve", modifier = Modifier.size(16.dp))
                Spacer(modifier = Modifier.width(4.dp))
                Text("Execute", fontWeight = FontWeight.Bold)
            }
        }
    }
}
