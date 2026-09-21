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
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.AlertDialog
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Switch
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
import com.precog.BuildConfig
import com.precog.data.SettingsStore
import com.precog.ui.components.Panel
import com.precog.ui.components.SectionLabel
import com.precog.ui.theme.Accent
import com.precog.ui.theme.Outline
import com.precog.ui.theme.Rust
import com.precog.ui.theme.TextSecondary
import com.precog.ui.vm.PrecogViewModel

/** WF-08. Control over what is watched, and an unconditional way out. */
@Composable
fun SettingsScreen(vm: PrecogViewModel) {
    val context = LocalContext.current
    val monitored by vm.monitoredApps.collectAsState()
    val pausedUntil by vm.pausedUntilMs.collectAsState()
    val sessions by vm.sessions.collectAsState()
    var confirmWipe by remember { mutableStateOf(false) }

    val paused = pausedUntil > System.currentTimeMillis()
    val captureOn = AccessibilityStatus.isEnabled(context)

    Column(
        Modifier
            .fillMaxSize()
            .verticalScroll(rememberScrollState())
            .padding(horizontal = 20.dp)
    ) {
        Spacer(Modifier.height(28.dp))
        Text("Settings", style = MaterialTheme.typography.headlineMedium)

        Spacer(Modifier.height(24.dp))
        SectionLabel("Recording")
        Spacer(Modifier.height(10.dp))
        Panel {
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text(
                        if (captureOn) "Accessibility permission is on" else "Accessibility permission is off",
                        fontWeight = FontWeight.Medium,
                    )
                    Text(
                        "Android controls this, not PRECOG.",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary,
                    )
                }
                OutlinedButton(
                    onClick = { AccessibilityStatus.openSettings(context) },
                    shape = RoundedCornerShape(10.dp),
                ) { Text(if (captureOn) "Change" else "Turn on") }
            }
            Spacer(Modifier.height(16.dp))
            Row(verticalAlignment = Alignment.CenterVertically) {
                Column(Modifier.weight(1f)) {
                    Text("Pause recording", fontWeight = FontWeight.Medium)
                    Text(
                        if (paused) "Paused until ${timeOf(pausedUntil)}"
                        else "PRECOG is recording in your chosen apps",
                        style = MaterialTheme.typography.bodySmall,
                        color = TextSecondary,
                    )
                }
                Switch(checked = paused, onCheckedChange = { if (it) vm.pauseFor(8) else vm.resume() })
            }
            if (!paused) {
                Spacer(Modifier.height(12.dp))
                Row(horizontalArrangement = Arrangement.spacedBy(8.dp)) {
                    listOf(1, 8, 24).forEach { hours ->
                        OutlinedButton(
                            onClick = { vm.pauseFor(hours) },
                            shape = RoundedCornerShape(10.dp),
                        ) { Text(if (hours == 24) "1 day" else "${hours}h") }
                    }
                }
            }
        }

        Spacer(Modifier.height(24.dp))
        SectionLabel("Apps PRECOG watches")
        Spacer(Modifier.height(10.dp))
        SettingsStore.CATALOGUE.forEach { app ->
            Row(
                Modifier
                    .fillMaxWidth()
                    .clip(RoundedCornerShape(12.dp))
                    .clickable { vm.toggleApp(app.pkg) }
                    .padding(vertical = 12.dp, horizontal = 4.dp),
                verticalAlignment = Alignment.CenterVertically,
            ) {
                Box(
                    Modifier
                        .size(20.dp)
                        .clip(RoundedCornerShape(6.dp))
                        .background(if (app.pkg in monitored) Accent else Outline),
                    contentAlignment = Alignment.Center,
                ) {
                    if (app.pkg in monitored) {
                        Icon(
                            Icons.Filled.Check, null,
                            tint = MaterialTheme.colorScheme.onPrimary,
                            modifier = Modifier.size(14.dp),
                        )
                    }
                }
                Spacer(Modifier.padding(horizontal = 7.dp))
                Column(Modifier.weight(1f)) {
                    Text(app.label, style = MaterialTheme.typography.bodyLarge)
                    Text(app.note, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
                }
            }
        }

        Spacer(Modifier.height(24.dp))
        SectionLabel("Your data")
        Spacer(Modifier.height(10.dp))
        Panel {
            Bullet("Stored only on this phone, encrypted with a key held in secure hardware")
            Bullet("No network permission is declared, so nothing can be uploaded")
            Bullet("Raw scroll timings are deleted after 48 hours")
            Bullet("${sessions.size} sessions currently stored")
        }

        Spacer(Modifier.height(12.dp))
        Panel(accent = Rust) {
            Text("Delete everything", fontWeight = FontWeight.Medium, color = Rust)
            Spacer(Modifier.height(8.dp))
            Text(
                "Removes every session, every learned pattern, and the encryption key itself. " +
                    "There is no backup and no way to undo it.",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
            )
            Spacer(Modifier.height(12.dp))
            OutlinedButton(onClick = { confirmWipe = true }, shape = RoundedCornerShape(10.dp)) {
                Text("Delete everything", color = Rust)
            }
        }

        Spacer(Modifier.height(24.dp))
        SectionLabel("About")
        Spacer(Modifier.height(10.dp))
        Panel {
            Text(
                "PRECOG ${BuildConfig.VERSION_NAME}",
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Medium,
            )
            Spacer(Modifier.height(8.dp))
            Text(
                "A research prototype. It describes how your scrolling compares to your own " +
                    "earlier scrolling. It is not a medical or diagnostic tool, it does not detect " +
                    "addiction, and none of its states are clinical findings.",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
            )
            Spacer(Modifier.height(10.dp))
            Text(
                "Detection accuracy has not been measured on this phone's feature set. The offline " +
                    "study that informed the method used touch kinematics an Android app cannot " +
                    "read, so its numbers do not carry over and are not claimed here.",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
            )
        }
        Spacer(Modifier.height(48.dp))
    }

    if (confirmWipe) {
        AlertDialog(
            onDismissRequest = { confirmWipe = false },
            title = { Text("Delete everything?") },
            text = {
                Text(
                    "Every session, every learned pattern and the encryption key will be destroyed. " +
                        "This cannot be undone."
                )
            },
            confirmButton = {
                TextButton(onClick = {
                    vm.deleteEverything()
                    confirmWipe = false
                }) { Text("Delete", color = Rust) }
            },
            dismissButton = {
                TextButton(onClick = { confirmWipe = false }) { Text("Keep my data") }
            },
        )
    }
}
