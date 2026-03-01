package com.trading.autopilot.ui.theme

import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp

// ── Dark Color Scheme ─────────────────────────────────────────────
private val TradingDarkColorScheme = darkColorScheme(
    primary = ElectricCyan,
    onPrimary = DeepNavy,
    secondary = NeonGreen,
    onSecondary = DeepNavy,
    tertiary = ElectricPurple,
    background = DeepNavy,
    surface = DarkSurface,
    surfaceVariant = CardSurface,
    onBackground = TextPrimary,
    onSurface = TextPrimary,
    onSurfaceVariant = TextSecondary,
    error = HotCoral,
    onError = DeepNavy,
    outline = CardBorder,
)

// ── Typography ────────────────────────────────────────────────────
val TradingTypography = Typography(
    displayLarge = TextStyle(
        fontWeight = FontWeight.Bold,
        fontSize = 32.sp,
        letterSpacing = (-0.5).sp,
        color = TextPrimary
    ),
    headlineLarge = TextStyle(
        fontWeight = FontWeight.Bold,
        fontSize = 24.sp,
        letterSpacing = 0.sp,
        color = TextPrimary
    ),
    headlineMedium = TextStyle(
        fontWeight = FontWeight.SemiBold,
        fontSize = 20.sp,
        letterSpacing = 0.sp,
        color = TextPrimary
    ),
    titleLarge = TextStyle(
        fontWeight = FontWeight.SemiBold,
        fontSize = 18.sp,
        letterSpacing = 0.sp,
        color = TextPrimary
    ),
    titleMedium = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 16.sp,
        letterSpacing = 0.15.sp,
        color = TextPrimary
    ),
    bodyLarge = TextStyle(
        fontWeight = FontWeight.Normal,
        fontSize = 16.sp,
        letterSpacing = 0.5.sp,
        color = TextSecondary
    ),
    bodyMedium = TextStyle(
        fontWeight = FontWeight.Normal,
        fontSize = 14.sp,
        letterSpacing = 0.25.sp,
        color = TextSecondary
    ),
    labelLarge = TextStyle(
        fontWeight = FontWeight.SemiBold,
        fontSize = 14.sp,
        letterSpacing = 0.1.sp,
        color = TextPrimary
    ),
    labelSmall = TextStyle(
        fontWeight = FontWeight.Medium,
        fontSize = 11.sp,
        letterSpacing = 0.5.sp,
        color = TextMuted
    ),
)

@Composable
fun TradingAutopilotTheme(content: @Composable () -> Unit) {
    MaterialTheme(
        colorScheme = TradingDarkColorScheme,
        typography = TradingTypography,
        content = content
    )
}
