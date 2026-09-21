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
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.produceState
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.precog.data.SettingsStore
import com.precog.engine.BaselineEngine
import com.precog.engine.CellBaseline
import com.precog.features.ContextCell
import com.precog.features.Feature
import com.precog.ui.components.ConfidenceMeter
import com.precog.ui.components.EnrolmentProgress
import com.precog.ui.components.Panel
import com.precog.ui.components.Readout
import com.precog.ui.components.SectionLabel
import com.precog.ui.theme.TextSecondary
import com.precog.ui.vm.PrecogViewModel
import kotlin.math.exp
import kotlin.math.roundToInt

/**
 * WF-06. What PRECOG has actually learned, in units a person can check against their own sense
 * of themselves.
 *
 * Each context gets its own card because the same person genuinely scrolls differently on
 * Reddit at lunchtime and on Instagram at midnight — that is the premise of the whole method,
 * so it should be visible rather than assumed.
 */
@Composable
fun PatternsScreen(vm: PrecogViewModel) {
    val cells by vm.baselineCells.collectAsState()
    val windows by vm.windowCount.collectAsState()

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp)
    ) {
        Spacer(Modifier.height(28.dp))
        Text("Your patterns", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(8.dp))
        Text(
            "One pattern per app and time of day. PRECOG compares a session only against the " +
                "pattern for that same context.",
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondary,
        )
        Spacer(Modifier.height(24.dp))

        if (cells.isEmpty()) {
            Panel {
                Text("No pattern learned yet", fontWeight = FontWeight.Medium)
                Spacer(Modifier.height(12.dp))
                EnrolmentProgress(windows, BaselineEngine.MIN_CELL_WINDOWS)
                Spacer(Modifier.height(10.dp))
                Text(
                    "$windows readings collected. A context needs about " +
                        "${BaselineEngine.MIN_CELL_WINDOWS} of them before PRECOG will model it.",
                    style = MaterialTheme.typography.bodyMedium,
                )
                Spacer(Modifier.height(8.dp))
                Text(
                    "Each reading is twenty scroll steps in a row. Android reports several steps per " +
                        "swipe as a flick slows down, so this is roughly " +
                        "${BaselineEngine.MIN_CELL_WINDOWS * 20 / 5} swipes in one app at one time of day.",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary,
                )
            }
        }

        cells.forEach { cell ->
            val baseline by produceState<CellBaseline?>(initialValue = null, cell.cellKey, cell.updatedMs) {
                value = vm.baselineFor(cell.cellKey)
            }
            Panel {
                Text(
                    "${SettingsStore.labelFor(cell.pkg)} · ${ContextCell.bucketLabel(cell.bucket)}",
                    style = MaterialTheme.typography.titleMedium,
                )
                Spacer(Modifier.height(4.dp))
                Text(
                    "Built from ${cell.n} readings",
                    style = MaterialTheme.typography.bodySmall,
                    color = TextSecondary,
                )

                val b = baseline
                if (b != null) {
                    Spacer(Modifier.height(14.dp))
                    ConfidenceMeter(b.confidence, confidenceLabel(b.confidence))
                    Spacer(Modifier.height(18.dp))
                    Row(Modifier.fillMaxWidth(), horizontalArrangement = Arrangement.SpaceBetween) {
                        Readout("between steps", formatGap(b.centres[Feature.MEDIAN_GAP.index]))
                        Readout("steps / sec", String.format("%.1f", b.centres[Feature.EVENT_RATE.index]))
                        Readout(
                            "unbroken",
                            "${(b.centres[Feature.UNBROKEN_RATIO.index] * 100).roundToInt()}%"
                        )
                    }
                    if (b.confidence < 0.35) {
                        Spacer(Modifier.height(14.dp))
                        Text(
                            "Your scrolling in this context varies too much for PRECOG to call anything " +
                                "unusual here. It will keep watching, but it may never settle — not " +
                                "everyone has a steady enough rhythm for this to work, and pretending " +
                                "otherwise would just produce noise.",
                            style = MaterialTheme.typography.bodySmall,
                            color = TextSecondary,
                        )
                    }
                }
            }
            Spacer(Modifier.height(12.dp))
        }

        Spacer(Modifier.height(20.dp))
        SectionLabel("How a reading is judged")
        Spacer(Modifier.height(10.dp))
        Panel {
            Text(
                "Two detectors run over each reading. One asks how likely that combination of " +
                    "timings is under the pattern PRECOG has learned for you. The other compresses " +
                    "the reading down to its main axes of variation and measures how much is left " +
                    "over. Whichever reacts more strongly sets the score.",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary,
            )
            Spacer(Modifier.height(12.dp))
            Text(
                "Contexts with few readings borrow from your overall pattern, in proportion to how " +
                    "little data they have. This is why a new app does not immediately start " +
                    "flagging things.",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary,
            )
        }
        Spacer(Modifier.height(48.dp))
    }
}

private fun formatGap(logMs: Double): String {
    val ms = exp(logMs)
    return if (ms >= 1000) String.format("%.1fs", ms / 1000.0) else "${ms.roundToInt()}ms"
}
