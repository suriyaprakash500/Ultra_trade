package com.trading.autopilot.ui.components

import androidx.compose.animation.animateColorAsState
import androidx.compose.animation.core.*
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.shape.CircleShape
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Brush
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.trading.autopilot.ui.theme.*

/**
 * Glassmorphic card with frosted border effect.
 */
@Composable
fun GlassCard(
    modifier: Modifier = Modifier,
    content: @Composable ColumnScope.() -> Unit
) {
    Card(
        modifier = modifier
            .fillMaxWidth()
            .border(1.dp, CardBorder.copy(alpha = 0.5f), RoundedCornerShape(16.dp)),
        shape = RoundedCornerShape(16.dp),
        colors = CardDefaults.cardColors(containerColor = CardSurface.copy(alpha = 0.85f)),
        elevation = CardDefaults.cardElevation(defaultElevation = 0.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp),
            content = content
        )
    }
}

/**
 *  P&L value with automatic green/red coloring.
 */
@Composable
fun PnlText(
    value: Double,
    prefix: String = "₹",
    suffix: String = "",
    fontSize: Int = 20,
    showSign: Boolean = true
) {
    val color = when {
        value > 0 -> BullishGreen
        value < 0 -> BearishRed
        else -> TextSecondary
    }
    val sign = if (showSign && value > 0) "+" else ""
    Text(
        text = "$sign$prefix${String.format("%,.2f", value)}$suffix",
        color = color,
        fontSize = fontSize.sp,
        fontWeight = FontWeight.Bold
    )
}

/**
 * Portfolio stat item (label + value).
 */
@Composable
fun StatItem(
    label: String,
    value: String,
    valueColor: Color = TextPrimary,
    modifier: Modifier = Modifier
) {
    Column(
        modifier = modifier,
        horizontalAlignment = Alignment.CenterHorizontally
    ) {
        Text(
            text = value,
            color = valueColor,
            fontSize = 16.sp,
            fontWeight = FontWeight.Bold
        )
        Spacer(modifier = Modifier.height(2.dp))
        Text(
            text = label,
            color = TextMuted,
            fontSize = 11.sp,
            fontWeight = FontWeight.Medium
        )
    }
}

/**
 * Sentiment badge (bullish/bearish/neutral).
 */
@Composable
fun SentimentBadge(sentiment: String) {
    val (color, emoji) = when (sentiment.lowercase()) {
        "very_bullish" -> BullishGreen to "🟢"
        "bullish" -> BullishGreen to "🟢"
        "neutral" -> NeutralGray to "⚪"
        "bearish" -> BearishRed to "🔴"
        "very_bearish" -> BearishRed to "🔴"
        else -> NeutralGray to "⚪"
    }
    Surface(
        shape = RoundedCornerShape(8.dp),
        color = color.copy(alpha = 0.15f),
        modifier = Modifier.padding(2.dp)
    ) {
        Text(
            text = "$emoji ${sentiment.replace("_", " ").uppercase()}",
            color = color,
            fontSize = 11.sp,
            fontWeight = FontWeight.SemiBold,
            modifier = Modifier.padding(horizontal = 8.dp, vertical = 4.dp)
        )
    }
}

/**
 * Pulsing kill switch button.
 */
@Composable
fun KillSwitchButton(
    isActive: Boolean,
    isLoading: Boolean,
    onClick: () -> Unit,
    modifier: Modifier = Modifier
) {
    val infiniteTransition = rememberInfiniteTransition(label = "kill_pulse")
    val pulseAlpha by infiniteTransition.animateFloat(
        initialValue = 0.6f,
        targetValue = 1f,
        animationSpec = infiniteRepeatable(
            animation = tween(800, easing = EaseInOutCubic),
            repeatMode = RepeatMode.Reverse
        ),
        label = "pulse"
    )

    val bgColor = if (isActive) {
        Brush.horizontalGradient(
            listOf(GradientKillStart.copy(alpha = pulseAlpha), GradientKillEnd)
        )
    } else {
        Brush.horizontalGradient(listOf(StatusDanger.copy(alpha = 0.3f), StatusDanger.copy(alpha = 0.2f)))
    }

    Button(
        onClick = onClick,
        enabled = !isLoading,
        modifier = modifier
            .fillMaxWidth()
            .height(52.dp),
        shape = RoundedCornerShape(12.dp),
        colors = ButtonDefaults.buttonColors(containerColor = Color.Transparent),
        contentPadding = PaddingValues(0.dp)
    ) {
        Box(
            modifier = Modifier
                .fillMaxSize()
                .background(bgColor, RoundedCornerShape(12.dp)),
            contentAlignment = Alignment.Center
        ) {
            if (isLoading) {
                CircularProgressIndicator(
                    modifier = Modifier.size(24.dp),
                    color = Color.White,
                    strokeWidth = 2.dp
                )
            } else {
                Text(
                    text = if (isActive) "⚠️ KILL SWITCH ACTIVE — TAP TO DEACTIVATE" else "🛑 EMERGENCY KILL SWITCH",
                    color = Color.White,
                    fontWeight = FontWeight.Bold,
                    fontSize = 14.sp
                )
            }
        }
    }
}

/**
 * Confidence progress bar.
 */
@Composable
fun ConfidenceBar(confidence: Double, modifier: Modifier = Modifier) {
    val color = when {
        confidence >= 80 -> BullishGreen
        confidence >= 60 -> AmberWarning
        else -> BearishRed
    }

    Column(modifier = modifier) {
        Row(
            horizontalArrangement = Arrangement.SpaceBetween,
            modifier = Modifier.fillMaxWidth()
        ) {
            Text("Confidence", color = TextMuted, fontSize = 11.sp)
            Text("${confidence.toInt()}%", color = color, fontSize = 11.sp, fontWeight = FontWeight.Bold)
        }
        Spacer(modifier = Modifier.height(4.dp))
        LinearProgressIndicator(
            progress = { (confidence / 100).toFloat() },
            modifier = Modifier
                .fillMaxWidth()
                .height(4.dp)
                .clip(RoundedCornerShape(2.dp)),
            color = color,
            trackColor = CardBorder,
        )
    }
}

/**
 * Section header with optional action.
 */
@Composable
fun SectionHeader(
    title: String,
    action: String? = null,
    onAction: (() -> Unit)? = null
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .padding(horizontal = 16.dp, vertical = 8.dp),
        horizontalArrangement = Arrangement.SpaceBetween,
        verticalAlignment = Alignment.CenterVertically
    ) {
        Text(
            text = title,
            color = TextPrimary,
            fontSize = 18.sp,
            fontWeight = FontWeight.SemiBold
        )
        if (action != null && onAction != null) {
            TextButton(onClick = onAction) {
                Text(text = action, color = ElectricCyan, fontSize = 13.sp)
            }
        }
    }
}
