package com.precog.ui.theme

import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Typography
import androidx.compose.material3.darkColorScheme
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.text.TextStyle
import androidx.compose.ui.text.font.FontFamily
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.sp
import com.precog.engine.BehaviouralState

// The palette is carried over from the figures and the prototype so the paper, the
// wireframes and the running app all read as one piece of work.
val Ink = Color(0xFF070A12)
val Surface1 = Color(0xFF10151F)
val Surface2 = Color(0xFF171D2A)
val Outline = Color(0xFF273040)
val TextPrimary = Color(0xFFE6E9F0)
val TextSecondary = Color(0xFF8A95A8)

val Accent = Color(0xFF4C7DD9)
val AccentDeep = Color(0xFF1F3B73)
val Sage = Color(0xFF5F9C8B)
val Amber = Color(0xFFD1A053)
val Rust = Color(0xFFC25A42)
val Ember = Color(0xFFD08048)

private val scheme = darkColorScheme(
    primary = Accent,
    onPrimary = Ink,
    secondary = Sage,
    background = Ink,
    onBackground = TextPrimary,
    surface = Surface1,
    onSurface = TextPrimary,
    surfaceVariant = Surface2,
    onSurfaceVariant = TextSecondary,
    outline = Outline,
    error = Rust,
)

/** Numbers are set in monospace so readings line up column-wise and read as measurements. */
val Mono = FontFamily.Monospace

private val typography = Typography(
    displaySmall = TextStyle(fontSize = 34.sp, fontWeight = FontWeight.Light, letterSpacing = (-0.5).sp),
    headlineMedium = TextStyle(fontSize = 25.sp, fontWeight = FontWeight.Normal, letterSpacing = (-0.3).sp),
    titleLarge = TextStyle(fontSize = 19.sp, fontWeight = FontWeight.Medium),
    titleMedium = TextStyle(fontSize = 16.sp, fontWeight = FontWeight.Medium),
    bodyLarge = TextStyle(fontSize = 15.sp, lineHeight = 23.sp),
    bodyMedium = TextStyle(fontSize = 14.sp, lineHeight = 21.sp),
    bodySmall = TextStyle(fontSize = 12.5.sp, lineHeight = 18.sp),
    labelLarge = TextStyle(fontSize = 13.sp, fontWeight = FontWeight.Medium, letterSpacing = 0.4.sp),
    labelSmall = TextStyle(fontSize = 11.sp, fontWeight = FontWeight.Medium, letterSpacing = 1.2.sp),
)

@Composable
fun PrecogTheme(content: @Composable () -> Unit) {
    @Suppress("UNUSED_EXPRESSION") isSystemInDarkTheme() // PRECOG is dark-only by design.
    MaterialTheme(colorScheme = scheme, typography = typography, content = content)
}

fun BehaviouralState.color(): Color = when (this) {
    BehaviouralState.LEARNING -> Accent
    BehaviouralState.NOT_ENOUGH_PATTERN -> TextSecondary
    BehaviouralState.NORMAL -> Sage
    BehaviouralState.ENGAGED -> Accent
    BehaviouralState.DISTRACTED -> Amber
    BehaviouralState.COMPULSIVE -> Ember
    BehaviouralState.HIGH_RISK -> Rust
}
