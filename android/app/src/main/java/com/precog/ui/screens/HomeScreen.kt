package com.precog.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ChevronRight
import androidx.compose.material.icons.filled.WarningAmber
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.precog.AccessibilityStatus
import com.precog.data.PrecogRepository
import com.precog.data.SettingsStore
import com.precog.engine.BaselineEngine
import com.precog.engine.BehaviouralState
import com.precog.ui.components.ConfidenceMeter
import com.precog.ui.components.EnrolmentProgress
import com.precog.ui.components.EvidenceRow
import com.precog.ui.components.Panel
import com.precog.ui.components.Readout
import com.precog.ui.components.SectionLabel
import com.precog.ui.components.StateDot
import com.precog.ui.theme.Amber
import com.precog.ui.theme.Sage
import com.precog.ui.theme.Surface2
import com.precog.ui.theme.TextSecondary
import com.precog.ui.theme.color
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import kotlin.math.roundToInt

/**
 * WF-03 and WF-04 on one surface — the reading, or the honest reason there is not one yet.
 *
 * The state is the headline and the evidence sits directly under it. A score with no evidence
 * behind it is not something this app is willing to show.
 */
@Composable
fun HomeScreen(
    vm: com.precog.ui.vm.PrecogViewModel,
    onOpenSession: (Long) -> Unit,
    onOpenPatterns: () -> Unit,
) {
    val context = LocalContext.current
    val state by vm.currentState.collectAsState()
    val latest by vm.latestScored.collectAsState()
    val today by vm.todaySessions.collectAsState()
    val windows by vm.windowCount.collectAsState()
    val pausedUntil by vm.pausedUntilMs.collectAsState()

    var acknowledged by remember { mutableStateOf(false) }
    val captureOn = AccessibilityStatus.isEnabled(context)
    val paused = pausedUntil > System.currentTimeMillis()

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp)
    ) {
        Spacer(Modifier.height(28.dp))
        Row(Modifier.fillMaxWidth(), verticalAlignment = Alignment.CenterVertically) {
            Text("PRECOG", style = MaterialTheme.typography.labelSmall, color = TextSecondary)
            Spacer(Modifier.weight(1f))
            CaptureChip(captureOn = captureOn && !paused, paused = paused)
        }
        Spacer(Modifier.height(24.dp))

        if (!captureOn) {
            Panel(accent = Amber) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    Icon(Icons.Filled.WarningAmber, null, tint = Amber)
                    Spacer(Modifier.padding(horizontal = 6.dp))
                    Text("Nothing is being recorded", fontWeight = FontWeight.Medium)
                }
                Spacer(Modifier.height(8.dp))
                Text(
                    "The accessibility permission is off, so PRECOG is not seeing any scrolling.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary,
                )
                Spacer(Modifier.height(12.dp))
                OutlinedButton(
                    onClick = { AccessibilityStatus.openSettings(context) },
                    shape = RoundedCornerShape(10.dp),
                ) { Text("Turn it on") }
            }
            Spacer(Modifier.height(16.dp))
        }

        // The headline reading.
        Panel(accent = state.color()) {
            Row(verticalAlignment = Alignment.CenterVertically) {
                StateDot(state, 12.dp)
                Spacer(Modifier.padding(horizontal = 5.dp))
                Text(
                    state.title.uppercase(),
                    style = MaterialTheme.typography.labelSmall,
                    color = state.color(),
                )
            }
            Spacer(Modifier.height(14.dp))
            Text(state.summary, style = MaterialTheme.typography.bodyLarge)

            val session = latest
            if (state == BehaviouralState.LEARNING) {
                Spacer(Modifier.height(20.dp))
                LearningDetail(windows)
            } else if (session != null) {
                Spacer(Modifier.height(18.dp))
                ConfidenceMeter(session.confidence, confidenceLabel(session.confidence))
                Spacer(Modifier.height(18.dp))
                Text(
                    "${SettingsStore.labelFor(session.pkg)} · ${timeOf(session.startMs)} · " +
                        "${((session.endMs - session.startMs) / 60000.0).roundToInt()} min",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary,
                )
            }
        }

        // Evidence for the headline, never more than two lines deep.
        val session = latest
        if (session != null && state != BehaviouralState.LEARNING) {
            val evidence = remember(session.id) { PrecogRepository.evidenceFromJson(session.evidenceJson) }
            if (evidence.isNotEmpty()) {
                Spacer(Modifier.height(24.dp))
                SectionLabel("What led to this")
                Spacer(Modifier.height(4.dp))
                evidence.take(2).forEachIndexed { i, e -> EvidenceRow(e, state, showCentreLabel = i == 0) }
                TextButton(onClick = { onOpenSession(session.id) }) {
                    Text("See all six signals")
                    Icon(Icons.Filled.ChevronRight, null, Modifier.padding(start = 2.dp))
                }
            }

            // Acting on the reading, with a response that actually responds (evaluation finding F-03).
            if (state.isAlerting) {
                Spacer(Modifier.height(8.dp))
                if (acknowledged || session.feedback != null) {
                    Panel(accent = Sage) {
                        Text("Noted — thank you", fontWeight = FontWeight.Medium, color = Sage)
                        Spacer(Modifier.height(6.dp))
                        Text(
                            "PRECOG will keep this session in your history but will not raise it again. " +
                                "Sessions you mark are used to judge how well the model is calling things.",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextSecondary,
                        )
                    }
                } else {
                    Panel {
                        Text("Does this match how it felt?", fontWeight = FontWeight.Medium)
                        Spacer(Modifier.height(12.dp))
                        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                            OutlinedButton(
                                onClick = { vm.recordFeedback(session.id, true); acknowledged = true },
                                shape = RoundedCornerShape(10.dp),
                                modifier = Modifier.weight(1f),
                            ) { Text("Yes, that was me") }
                            OutlinedButton(
                                onClick = { vm.recordFeedback(session.id, false); acknowledged = true },
                                shape = RoundedCornerShape(10.dp),
                                modifier = Modifier.weight(1f),
                            ) { Text("No, that was fine") }
                        }
                    }
                }
            }
        }

        Spacer(Modifier.height(28.dp))
        SectionLabel("Today")
        Spacer(Modifier.height(12.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Readout("sessions", today.size.toString())
            Readout("scroll steps", today.sumOf { it.eventCount }.toString())
            Readout(
                "flagged",
                today.count { BehaviouralState.fromOrdinal(it.stateOrdinal)?.isAlerting == true }.toString()
            )
        }

        Spacer(Modifier.height(24.dp))
        Row(
            Modifier
                .fillMaxWidth()
                .clip(RoundedCornerShape(12.dp))
                .clickable(onClick = onOpenPatterns)
                .padding(vertical = 14.dp),
            verticalAlignment = Alignment.CenterVertically,
        ) {
            Text("See the pattern PRECOG has learned", style = MaterialTheme.typography.bodyMedium)
            Spacer(Modifier.weight(1f))
            Icon(Icons.Filled.ChevronRight, null, tint = TextSecondary)
        }
        Spacer(Modifier.height(40.dp))
    }
}

/**
 * WF-04. During enrolment the app says what it is waiting for and how far along it is,
 * rather than showing an empty dashboard or a placeholder number.
 */
@Composable
private fun LearningDetail(windows: Int) {
    val target = BaselineEngine.MIN_CELL_WINDOWS
    Column {
        EnrolmentProgress(windows, target)
        Spacer(Modifier.height(10.dp))
        Text(
            if (windows == 0) "No scrolling recorded yet in the apps you chose."
            else "$windows of about $target readings collected.",
            style = MaterialTheme.typography.bodyMedium,
        )
        Spacer(Modifier.height(8.dp))
        Text(
            "PRECOG needs enough of your scrolling in one app at one time of day before it will " +
                "call anything unusual. Keep using your phone as you normally would — changing how " +
                "you scroll now would only teach it the wrong pattern.",
            style = MaterialTheme.typography.bodySmall,
            color = TextSecondary,
        )
    }
}

@Composable
private fun CaptureChip(captureOn: Boolean, paused: Boolean) {
    val tint = when {
        paused -> Amber
        captureOn -> Sage
        else -> TextSecondary
    }
    Row(
        Modifier
            .clip(RoundedCornerShape(50))
            .background(Surface2)
            .padding(horizontal = 10.dp, vertical = 5.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            Modifier
                .padding(end = 6.dp)
                .size(7.dp)
                .clip(RoundedCornerShape(50))
                .background(tint)
        )
        Text(
            when {
                paused -> "Paused"
                captureOn -> "Recording"
                else -> "Off"
            },
            style = MaterialTheme.typography.bodySmall,
            color = tint,
        )
    }
}

internal fun confidenceLabel(confidence: Double): String = when {
    confidence >= 0.75 -> "High"
    confidence >= 0.50 -> "Moderate"
    else -> "Low"
}

internal fun timeOf(ms: Long): String =
    SimpleDateFormat("h:mm a", Locale.getDefault()).format(Date(ms))

internal fun dayOf(ms: Long): String =
    SimpleDateFormat("EEE d MMM", Locale.getDefault()).format(Date(ms))
