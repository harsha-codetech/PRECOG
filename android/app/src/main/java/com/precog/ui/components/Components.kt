package com.precog.ui.components

import androidx.compose.animation.core.animateFloatAsState
import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.getValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.geometry.Offset
import androidx.compose.ui.geometry.Size
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.drawscope.Stroke
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import androidx.compose.foundation.Canvas
import com.precog.engine.BehaviouralState
import com.precog.features.FeatureEvidence
import com.precog.ui.theme.Mono
import com.precog.ui.theme.Outline
import com.precog.ui.theme.Sage
import com.precog.ui.theme.Surface1
import com.precog.ui.theme.Surface2
import com.precog.ui.theme.TextSecondary
import com.precog.ui.theme.color
import kotlin.math.abs

/** Section heading used throughout, so every screen is read the same way. */
@Composable
fun SectionLabel(text: String, modifier: Modifier = Modifier) {
    Text(
        text.uppercase(),
        style = MaterialTheme.typography.labelSmall,
        color = TextSecondary,
        modifier = modifier,
    )
}

@Composable
fun Panel(
    modifier: Modifier = Modifier,
    accent: Color? = null,
    content: @Composable androidx.compose.foundation.layout.ColumnScope.() -> Unit,
) {
    Column(
        modifier = modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(16.dp))
            .background(Surface1)
            .border(1.dp, accent?.copy(alpha = 0.35f) ?: Outline, RoundedCornerShape(16.dp))
            .padding(18.dp),
        content = content,
    )
}

/**
 * The tolerance band: where one reading sits against the range this person usually occupies.
 *
 * The usual range is drawn, not stated as a number, and the centre line is labelled in
 * words. This replaces the sigma readout the heuristic evaluation flagged (F-07): a
 * position on a band answers "is this far?" without asking anyone to know what sigma means.
 */
@Composable
fun ToleranceBand(
    sigma: Double,
    tint: Color,
    showCentreLabel: Boolean = false,
    modifier: Modifier = Modifier,
) {
    val clamped = sigma.coerceIn(-RANGE, RANGE).toFloat()
    val position by animateFloatAsState(
        targetValue = (clamped + RANGE.toFloat()) / (2 * RANGE.toFloat()),
        label = "band",
    )

    Column(modifier) {
        Canvas(
            Modifier
                .fillMaxWidth()
                .height(28.dp)
        ) {
            val trackY = size.height / 2
            val trackHeight = 8.dp.toPx()

            // Full observable range.
            drawRoundRect(
                color = Outline.copy(alpha = 0.45f),
                topLeft = Offset(0f, trackY - trackHeight / 2),
                size = Size(size.width, trackHeight),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(trackHeight / 2),
            )

            // The band the person usually occupies.
            val usualHalf = (USUAL_SIGMA / RANGE).toFloat() / 2f * size.width
            drawRoundRect(
                color = Sage.copy(alpha = 0.22f),
                topLeft = Offset(size.width / 2 - usualHalf, trackY - trackHeight / 2),
                size = Size(usualHalf * 2, trackHeight),
                cornerRadius = androidx.compose.ui.geometry.CornerRadius(trackHeight / 2),
            )

            // Centre line: the person's own usual value.
            drawLine(
                color = Sage.copy(alpha = 0.85f),
                start = Offset(size.width / 2, trackY - 9.dp.toPx()),
                end = Offset(size.width / 2, trackY + 9.dp.toPx()),
                strokeWidth = 1.5.dp.toPx(),
            )

            // This reading.
            val x = position * size.width
            drawCircle(color = tint, radius = 6.dp.toPx(), center = Offset(x, trackY))
            drawCircle(
                color = tint.copy(alpha = 0.35f),
                radius = 10.dp.toPx(),
                center = Offset(x, trackY),
                style = Stroke(width = 1.5.dp.toPx()),
            )
        }
        if (showCentreLabel) {
            Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.Center) {
                Text(
                    "your usual",
                    style = MaterialTheme.typography.labelSmall,
                    color = Sage.copy(alpha = 0.9f),
                )
            }
        }
    }
}

/**
 * One line of evidence, in plain language.
 *
 * Wording before numbers, and the numeric comparison is a ratio a person can picture
 * rather than a standard-deviation count.
 */
@Composable
fun EvidenceRow(evidence: FeatureEvidence, state: BehaviouralState, showCentreLabel: Boolean = false) {
    val tint = if (abs(evidence.sigma) < 1.0) TextSecondary else state.color()
    Column(Modifier.padding(vertical = 10.dp)) {
        Row(verticalAlignment = Alignment.CenterVertically) {
            Text(
                evidence.feature.label,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
                modifier = Modifier.weight(1f),
            )
            evidence.plainMagnitude?.let {
                Text(it, style = MaterialTheme.typography.bodySmall, color = TextSecondary, fontFamily = Mono)
            }
        }
        Spacer(Modifier.height(6.dp))
        ToleranceBand(evidence.sigma, tint, showCentreLabel)
        Spacer(Modifier.height(2.dp))
        Text(
            if (abs(evidence.sigma) < 1.0) "In your usual range"
            else "You were ${evidence.intensity} ${evidence.plainDirection}",
            style = MaterialTheme.typography.bodySmall,
            color = if (abs(evidence.sigma) < 1.0) TextSecondary else MaterialTheme.colorScheme.onSurface,
        )
    }
}

/**
 * How much the reading can be trusted. Confidence is shown next to every verdict because a
 * verdict without it invites more certainty than this method has earned.
 */
@Composable
fun ConfidenceMeter(confidence: Double, label: String, modifier: Modifier = Modifier) {
    val filled = (confidence * SEGMENTS).toInt().coerceIn(0, SEGMENTS)
    Row(modifier, verticalAlignment = Alignment.CenterVertically) {
        repeat(SEGMENTS) { i ->
            Box(
                Modifier
                    .width(16.dp)
                    .height(4.dp)
                    .clip(RoundedCornerShape(2.dp))
                    .background(if (i < filled) Sage else Outline)
            )
            Spacer(Modifier.width(3.dp))
        }
        Spacer(Modifier.width(8.dp))
        Text(
            "$label confidence",
            style = MaterialTheme.typography.bodySmall,
            color = TextSecondary,
        )
    }
}

/** Small key-value readout; the value is monospaced so a column of them aligns. */
@Composable
fun Readout(label: String, value: String, modifier: Modifier = Modifier) {
    Column(modifier) {
        Text(value, style = MaterialTheme.typography.titleMedium, fontFamily = Mono)
        Spacer(Modifier.height(2.dp))
        Text(label, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
    }
}

/** Progress toward having enough data to model one context. */
@Composable
fun EnrolmentProgress(current: Int, target: Int, modifier: Modifier = Modifier) {
    val fraction by animateFloatAsState(
        targetValue = (current.toFloat() / target).coerceIn(0f, 1f),
        label = "enrolment",
    )
    Column(modifier.fillMaxWidth()) {
        Box(
            Modifier
                .fillMaxWidth()
                .height(6.dp)
                .clip(RoundedCornerShape(3.dp))
                .background(Surface2)
        ) {
            Box(
                Modifier
                    .fillMaxWidth(fraction)
                    .height(6.dp)
                    .clip(RoundedCornerShape(3.dp))
                    .background(MaterialTheme.colorScheme.primary)
            )
        }
    }
}

@Composable
fun StateDot(state: BehaviouralState, size: androidx.compose.ui.unit.Dp = 10.dp) {
    Box(
        Modifier
            .size(size)
            .clip(RoundedCornerShape(50))
            .background(state.color())
    )
}

private const val RANGE = 4.0

/** Half-width of the band treated as ordinary, matching the DISTRACTED threshold. */
private const val USUAL_SIGMA = 1.5
private const val SEGMENTS = 4
