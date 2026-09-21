package com.precog.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.border
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Text
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.unit.dp
import com.precog.data.SettingsStore
import com.precog.data.db.SessionEntity
import com.precog.engine.BehaviouralState
import com.precog.ui.components.SectionLabel
import com.precog.ui.components.StateDot
import com.precog.ui.theme.Accent
import com.precog.ui.theme.Mono
import com.precog.ui.theme.Outline
import com.precog.ui.theme.Surface1
import com.precog.ui.theme.TextSecondary
import com.precog.ui.theme.color
import com.precog.ui.vm.PrecogViewModel
import kotlin.math.roundToInt

private enum class HistoryFilter(val label: String) {
    ALL("All"),
    FLAGGED("Flagged"),
    UNSCORED("Not scored"),
}

/**
 * WF-07. Every session, newest first, filterable.
 *
 * The filter exists because the evaluation found the flat list unusable once it grows past
 * a couple of days (F-16): the flagged sessions are the ones anybody comes here to find.
 */
@Composable
fun HistoryScreen(vm: PrecogViewModel, onOpenSession: (Long) -> Unit) {
    val sessions by vm.sessions.collectAsState()
    var filter by remember { mutableStateOf(HistoryFilter.ALL) }

    val visible = remember(sessions, filter) {
        when (filter) {
            HistoryFilter.ALL -> sessions
            HistoryFilter.FLAGGED -> sessions.filter {
                BehaviouralState.fromOrdinal(it.stateOrdinal)?.isAlerting == true
            }
            HistoryFilter.UNSCORED -> sessions.filter { it.stateOrdinal == null }
        }
    }

    Column(Modifier.fillMaxSize().padding(horizontal = 20.dp)) {
        Spacer(Modifier.height(28.dp))
        Text("History", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(16.dp))

        Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
            HistoryFilter.entries.forEach { f ->
                FilterChip(f.label, f == filter) { filter = f }
            }
        }
        Spacer(Modifier.height(20.dp))

        if (visible.isEmpty()) {
            SectionLabel(
                when (filter) {
                    HistoryFilter.ALL -> "No sessions recorded yet"
                    HistoryFilter.FLAGGED -> "Nothing has been flagged"
                    HistoryFilter.UNSCORED -> "Every session has been scored"
                }
            )
        }

        LazyColumn(verticalArrangement = Arrangement.spacedBy(8.dp)) {
            items(visible, key = { it.id }) { session ->
                SessionRow(session) { onOpenSession(session.id) }
            }
            item { Spacer(Modifier.height(32.dp)) }
        }
    }
}

@Composable
private fun FilterChip(label: String, selected: Boolean, onClick: () -> Unit) {
    Row(
        Modifier
            .clip(RoundedCornerShape(50))
            .background(if (selected) Accent.copy(alpha = 0.18f) else Color.Transparent)
            .border(1.dp, if (selected) Accent else Outline, RoundedCornerShape(50))
            .clickable(onClick = onClick)
            .padding(horizontal = 14.dp, vertical = 7.dp)
    ) {
        Text(
            label,
            style = MaterialTheme.typography.bodySmall,
            color = if (selected) Accent else TextSecondary,
        )
    }
}

@Composable
private fun SessionRow(session: SessionEntity, onClick: () -> Unit) {
    val state = BehaviouralState.fromOrdinal(session.stateOrdinal)
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(Surface1)
            .clickable(onClick = onClick)
            .padding(14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        if (state != null) StateDot(state) else StateDot(BehaviouralState.NOT_ENOUGH_PATTERN)
        Spacer(Modifier.padding(horizontal = 6.dp))
        Column(Modifier.weight(1f)) {
            Text(
                "${SettingsStore.labelFor(session.pkg)} · ${state?.title ?: "Not scored"}",
                style = MaterialTheme.typography.bodyMedium,
                color = state?.color() ?: TextSecondary,
            )
            Text(
                "${dayOf(session.startMs)}, ${timeOf(session.startMs)} · " +
                    "${session.eventCount} scroll steps · " +
                    "${((session.endMs - session.startMs) / 60000.0).roundToInt()} min",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
            )
        }
        session.peakScore?.let {
            Text(String.format("%.1f", it), style = MaterialTheme.typography.bodySmall, fontFamily = Mono, color = TextSecondary)
        }
    }
}
