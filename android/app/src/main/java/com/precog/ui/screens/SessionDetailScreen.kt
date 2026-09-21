package com.precog.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.automirrored.filled.ArrowBack
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.precog.data.PrecogRepository
import com.precog.data.SettingsStore
import com.precog.engine.BehaviouralState
import com.precog.features.ContextCell
import com.precog.ui.components.ConfidenceMeter
import com.precog.ui.components.EvidenceRow
import com.precog.ui.components.Panel
import com.precog.ui.components.Readout
import com.precog.ui.components.SectionLabel
import com.precog.ui.components.StateDot
import com.precog.ui.theme.Mono
import com.precog.ui.theme.TextSecondary
import com.precog.ui.theme.color
import com.precog.ui.vm.PrecogViewModel
import kotlin.math.roundToInt

/**
 * WF-05. The full evidence for one session.
 *
 * All six signals are shown, ranked by how far each one moved, including the ones that did
 * not move. Showing only the signals that support the verdict would make the verdict look
 * better than the evidence does.
 */
@Composable
fun SessionDetailScreen(vm: PrecogViewModel, sessionId: Long, onBack: () -> Unit) {
    val session by vm.session(sessionId).collectAsState(initial = null)

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp)
    ) {
        Spacer(Modifier.height(20.dp))
        Row(verticalAlignment = Alignment.CenterVertically) {
            IconButton(onClick = onBack) {
                Icon(Icons.AutoMirrored.Filled.ArrowBack, contentDescription = "Back", tint = TextSecondary)
            }
            Text("Session", style = MaterialTheme.typography.labelSmall, color = TextSecondary)
        }

        val s = session
        if (s == null) {
            Spacer(Modifier.height(40.dp))
            Text("That session is no longer stored.", color = TextSecondary)
            return@Column
        }

        val state = BehaviouralState.fromOrdinal(s.stateOrdinal)
        val evidence = remember(s.id, s.evidenceJson) { PrecogRepository.evidenceFromJson(s.evidenceJson) }

        Spacer(Modifier.height(12.dp))
        Text(
            "${SettingsStore.labelFor(s.pkg)} · ${dayOf(s.startMs)}",
            style = MaterialTheme.typography.titleLarge,
        )
        Spacer(Modifier.height(4.dp))
        Text(
            "${timeOf(s.startMs)} to ${timeOf(s.endMs)} · ${ContextCell.bucketLabel(s.bucket).lowercase()}",
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondary,
        )

        Spacer(Modifier.height(20.dp))
        if (state == null) {
            Panel {
                Text("Not scored", fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(8.dp))
                Text(
                    "This session was recorded before PRECOG had a baseline for " +
                        "${SettingsStore.labelFor(s.pkg)} in the ${ContextCell.bucketLabel(s.bucket).lowercase()}. " +
                        "It still counts toward building that baseline.",
                    style = MaterialTheme.typography.bodyMedium,
                    color = TextSecondary,
                )
            }
        } else {
            Panel(accent = state.color()) {
                Row(verticalAlignment = Alignment.CenterVertically) {
                    StateDot(state, 12.dp)
                    Spacer(Modifier.padding(horizontal = 5.dp))
                    Text(state.title.uppercase(), style = MaterialTheme.typography.labelSmall, color = state.color())
                }
                Spacer(Modifier.height(12.dp))
                Text(state.summary, style = MaterialTheme.typography.bodyLarge)
                Spacer(Modifier.height(16.dp))
                ConfidenceMeter(s.confidence, confidenceLabel(s.confidence))
            }
        }

        Spacer(Modifier.height(24.dp))
        Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
            Readout("scroll steps", s.eventCount.toString())
            Readout("readings", s.windowCount.toString())
            Readout("minutes", ((s.endMs - s.startMs) / 60000.0).roundToInt().toString())
        }

        if (evidence.isNotEmpty() && state != null) {
            Spacer(Modifier.height(28.dp))
            SectionLabel("All six signals, furthest first")
            Spacer(Modifier.height(4.dp))
            evidence.forEachIndexed { i, e -> EvidenceRow(e, state, showCentreLabel = i == 0) }
        }

        if (s.feedback != null) {
            Spacer(Modifier.height(16.dp))
            Panel {
                Text(
                    if (s.feedback == 1) "You marked this as a fair call."
                    else "You marked this as a false alarm.",
                    style = MaterialTheme.typography.bodyMedium,
                )
            }
        }

        // The technical readout stays available but stays last: the numbers behind the words,
        // for anyone who wants to check the working.
        if (state != null) {
            Spacer(Modifier.height(28.dp))
            SectionLabel("Under the hood")
            Spacer(Modifier.height(10.dp))
            Panel {
                TechRow("Deviation score", String.format("%.2f", s.peakScore ?: 0.0))
                TechRow("Median across readings", String.format("%.2f", s.medianScore ?: 0.0))
                TechRow("Context cell", "${SettingsStore.labelFor(s.pkg)} / ${ContextCell.bucketLabel(s.bucket)}")
                Spacer(Modifier.height(10.dp))
                Text(
                    "The score is how far this session sat outside your own spread, in robust standard " +
                        "deviations. It comes from whichever of the two detectors — density or " +
                        "reconstruction error — reacted more strongly.",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary,
                )
            }
        }
        Spacer(Modifier.height(48.dp))
    }
}

@Composable
private fun TechRow(label: String, value: String) {
    Row(Modifier.fillMaxWidth().padding(vertical = 5.dp)) {
        Text(label, style = MaterialTheme.typography.bodySmall, color = TextSecondary, modifier = Modifier.weight(1f))
        Text(value, style = MaterialTheme.typography.bodySmall, fontFamily = Mono)
    }
}
