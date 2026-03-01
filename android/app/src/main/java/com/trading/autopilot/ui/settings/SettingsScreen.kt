package com.trading.autopilot.ui.settings

import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import androidx.hilt.navigation.compose.hiltViewModel
import com.trading.autopilot.BuildConfig
import com.trading.autopilot.ui.components.*
import com.trading.autopilot.ui.theme.*

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SettingsScreen(
    viewModel: SettingsViewModel = hiltViewModel()
) {
    val state by viewModel.uiState.collectAsState()

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Settings", fontWeight = FontWeight.Bold) },
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
            verticalArrangement = Arrangement.spacedBy(12.dp),
            contentPadding = PaddingValues(vertical = 12.dp)
        ) {
            // ── Connection Status ─────────────────────────────
            item {
                GlassCard {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("Backend Connection", color = TextMuted, fontSize = 12.sp)
                            Spacer(modifier = Modifier.height(4.dp))
                            Row(verticalAlignment = Alignment.CenterVertically) {
                                Surface(
                                    shape = CircleShape,
                                    color = if (state.isConnected) StatusSuccess else StatusDanger,
                                    modifier = Modifier.size(10.dp)
                                ) {}
                                Spacer(modifier = Modifier.width(8.dp))
                                Text(
                                    if (state.isConnected) "Connected" else "Disconnected",
                                    color = if (state.isConnected) StatusSuccess else StatusDanger,
                                    fontWeight = FontWeight.SemiBold,
                                    fontSize = 14.sp
                                )
                            }
                        }
                        IconButton(onClick = { viewModel.checkConnection() }) {
                            if (state.isChecking) {
                                CircularProgressIndicator(
                                    modifier = Modifier.size(20.dp),
                                    color = ElectricCyan,
                                    strokeWidth = 2.dp
                                )
                            } else {
                                Icon(Icons.Default.Refresh, "Check", tint = ElectricCyan)
                            }
                        }
                    }

                    state.health?.let { health ->
                        Spacer(modifier = Modifier.height(8.dp))
                        HorizontalDivider(color = CardBorder)
                        Spacer(modifier = Modifier.height(8.dp))
                        Row(
                            modifier = Modifier.fillMaxWidth(),
                            horizontalArrangement = Arrangement.SpaceEvenly
                        ) {
                            StatItem("Version", health.version)
                            StatItem("Mode", health.trading_mode.uppercase(),
                                valueColor = AmberWarning
                            )
                            StatItem("Uptime", "${(health.uptime_seconds / 60).toInt()}m")
                        }
                    }
                }
            }

            // ── Backend URL ───────────────────────────────────
            item {
                GlassCard {
                    Text("Backend URL", color = TextMuted, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        BuildConfig.BASE_URL,
                        color = ElectricCyan,
                        fontSize = 14.sp,
                        fontWeight = FontWeight.Medium
                    )
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "Change in app/build.gradle.kts → BASE_URL",
                        color = TextMuted,
                        fontSize = 11.sp
                    )
                }
            }

            // ── Trading Mode ──────────────────────────────────
            item {
                GlassCard {
                    Row(
                        modifier = Modifier.fillMaxWidth(),
                        horizontalArrangement = Arrangement.SpaceBetween,
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Column {
                            Text("Trading Mode", color = TextMuted, fontSize = 12.sp)
                            Text(
                                "📝 PAPER TRADING",
                                color = AmberWarning,
                                fontSize = 16.sp,
                                fontWeight = FontWeight.Bold
                            )
                        }
                        Icon(Icons.Default.Shield, "Safe", tint = AmberWarning)
                    }
                    Spacer(modifier = Modifier.height(4.dp))
                    Text(
                        "No real money at risk. All trades are simulated.",
                        color = TextMuted,
                        fontSize = 12.sp
                    )
                }
            }

            // ── App Info ──────────────────────────────────────
            item {
                GlassCard {
                    Text("About", color = TextMuted, fontSize = 12.sp)
                    Spacer(modifier = Modifier.height(8.dp))
                    SettingRow("App Version", BuildConfig.VERSION_NAME)
                    SettingRow("API Level", "26+ (Android 8.0)")
                    SettingRow("AI Engine", "Grok (xAI)")
                    SettingRow("Risk Layers", "7 (institutional-grade)")
                }
            }

            state.error?.let { error ->
                item {
                    GlassCard {
                        Text("⚠️ $error", color = HotCoral, fontSize = 13.sp)
                    }
                }
            }

            item { Spacer(modifier = Modifier.height(80.dp)) }
        }
    }
}

@Composable
private fun SettingRow(label: String, value: String) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(vertical = 4.dp),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, color = TextSecondary, fontSize = 13.sp)
        Text(value, color = TextPrimary, fontSize = 13.sp, fontWeight = FontWeight.Medium)
    }
}
