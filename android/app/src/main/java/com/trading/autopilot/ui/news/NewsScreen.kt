package com.trading.autopilot.ui.news

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
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
fun NewsScreen(
    viewModel: NewsViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Market News", fontWeight = FontWeight.Bold) },
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
        if (state.isLoading && state.news.isEmpty()) {
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
                verticalArrangement = Arrangement.spacedBy(10.dp),
                contentPadding = PaddingValues(vertical = 12.dp)
            ) {
                state.error?.let { error ->
                    item {
                        GlassCard {
                            Text("⚠️ $error", color = HotCoral, fontSize = 13.sp)
                        }
                    }
                }

                if (state.news.isEmpty()) {
                    item {
                        GlassCard {
                            Column(
                                modifier = Modifier.fillMaxWidth(),
                                horizontalAlignment = Alignment.CenterHorizontally
                            ) {
                                Text("📰", fontSize = 40.sp)
                                Spacer(modifier = Modifier.height(8.dp))
                                Text("No news yet", color = TextPrimary, fontSize = 16.sp, fontWeight = FontWeight.SemiBold)
                                Text("Pull to refresh or run the morning routine", color = TextMuted, fontSize = 13.sp)
                            }
                        }
                    }
                }

                items(state.news) { article ->
                    GlassCard {
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceBetween,
                            verticalAlignment = Alignment.Top
                        ) {
                            Column(modifier = Modifier.weight(1f)) {
                                Text(
                                    article.title,
                                    color = TextPrimary,
                                    fontSize = 14.sp,
                                    fontWeight = FontWeight.Medium,
                                    maxLines = 2
                                )
                                Spacer(modifier = Modifier.height(4.dp))
                                Row(
                                    verticalAlignment = Alignment.CenterVertically,
                                    horizontalArrangement = Arrangement.spacedBy(6.dp)
                                ) {
                                    SentimentBadge(article.sentiment)
                                    if (article.impact_level != "low") {
                                        Text(
                                            "Impact: ${article.impact_level.uppercase()}",
                                            color = if (article.impact_level == "high") AmberWarning else TextMuted,
                                            fontSize = 10.sp,
                                            fontWeight = FontWeight.SemiBold
                                        )
                                    }
                                }
                            }
                        }

                        if (article.summary.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(6.dp))
                            Text(article.summary, color = TextMuted, fontSize = 12.sp, maxLines = 3)
                        }

                        if (article.affected_symbols.isNotEmpty()) {
                            Spacer(modifier = Modifier.height(4.dp))
                            Text(
                                article.affected_symbols.joinToString(" • "),
                                color = ElectricCyan,
                                fontSize = 11.sp,
                                fontWeight = FontWeight.SemiBold
                            )
                        }
                    }
                }

                item { Spacer(modifier = Modifier.height(80.dp)) }
            }
        }
    }
}
