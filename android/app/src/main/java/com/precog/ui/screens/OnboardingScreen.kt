package com.precog.ui.screens

import androidx.compose.foundation.background
import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.rememberScrollState
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.verticalScroll
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.Check
import androidx.compose.material3.Button
import androidx.compose.material3.Icon
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedButton
import androidx.compose.material3.Text
import androidx.compose.material3.TextButton
import androidx.compose.runtime.Composable
import androidx.compose.runtime.collectAsState
import androidx.compose.runtime.getValue
import androidx.compose.runtime.mutableIntStateOf
import androidx.compose.runtime.remember
import androidx.compose.runtime.setValue
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.draw.clip
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.unit.dp
import com.precog.AccessibilityStatus
import com.precog.data.SettingsStore
import com.precog.ui.components.Panel
import com.precog.ui.components.SectionLabel
import com.precog.ui.theme.Accent
import com.precog.ui.theme.Outline
import com.precog.ui.theme.Sage
import com.precog.ui.theme.Surface2
import com.precog.ui.theme.TextSecondary
import com.precog.ui.vm.PrecogViewModel

/**
 * WF-01 / WF-02. Three steps: what it does, what it never sees, what to turn on.
 *
 * Consent is a deliberate act on its own screen, and the page that asks for it is the page
 * that lists the limits. Nobody should be able to say yes without having read what yes covers.
 */
@Composable
fun OnboardingScreen(vm: PrecogViewModel, onDone: () -> Unit) {
    var step by remember { mutableIntStateOf(0) }
    val monitored by vm.monitoredApps.collectAsState()
    val context = LocalContext.current

    Column(
        Modifier
            .fillMaxSize()
            .padding(horizontal = 24.dp)
            .verticalScroll(rememberScrollState())
    ) {
        Spacer(Modifier.height(56.dp))
        Row {
            repeat(3) { i ->
                Box(
                    Modifier
                        .width(if (i == step) 28.dp else 12.dp)
                        .height(3.dp)
                        .clip(RoundedCornerShape(2.dp))
                        .background(if (i <= step) Accent else Outline)
                )
                Spacer(Modifier.width(6.dp))
            }
        }
        Spacer(Modifier.height(40.dp))

        when (step) {
            0 -> StepIntro()
            1 -> StepPrivacy()
            else -> StepSetup(monitored, vm)
        }

        Spacer(Modifier.height(32.dp))

        if (step < 2) {
            Button(
                onClick = { step++ },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
            ) { Text(if (step == 0) "Continue" else "I understand — start setup") }
        } else {
            Button(
                onClick = { AccessibilityStatus.openSettings(context) },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
            ) { Text("Open accessibility settings") }
            Spacer(Modifier.height(8.dp))
            OutlinedButton(
                onClick = {
                    vm.grantConsent()
                    vm.completeOnboarding()
                    onDone()
                },
                modifier = Modifier.fillMaxWidth(),
                shape = RoundedCornerShape(12.dp),
            ) { Text("Done — take me in") }
        }

        if (step > 0) {
            TextButton(onClick = { step-- }, modifier = Modifier.align(Alignment.CenterHorizontally)) {
                Text("Back", color = TextSecondary)
            }
        }
        Spacer(Modifier.height(32.dp))
    }
}

@Composable
private fun StepIntro() {
    Column {
        Text("PRECOG", style = MaterialTheme.typography.labelSmall, color = Accent)
        Spacer(Modifier.height(12.dp))
        Text(
            "It learns how you normally scroll, then tells you when you have drifted from it.",
            style = MaterialTheme.typography.headlineMedium,
        )
        Spacer(Modifier.height(20.dp))
        Text(
            "Not screen time. Not a limit. PRECOG compares you against your own rhythm — the pauses " +
                "between your scroll movements, how steady they are, how often you scroll back up.",
            style = MaterialTheme.typography.bodyLarge,
            color = TextSecondary,
        )
        Spacer(Modifier.height(24.dp))
        Panel {
            Text("Everything is your own baseline", fontWeight = FontWeight.Medium)
            Spacer(Modifier.height(8.dp))
            Text(
                "There is no normal to score you against. A slow scroller and a fast one both get " +
                    "their own model, built only from their own data on this phone.",
                style = MaterialTheme.typography.bodyMedium,
                color = TextSecondary,
            )
        }
    }
}

@Composable
private fun StepPrivacy() {
    Column {
        SectionLabel("What this can and cannot see")
        Spacer(Modifier.height(16.dp))
        Text("The limits are built in, not promised.", style = MaterialTheme.typography.headlineMedium)
        Spacer(Modifier.height(24.dp))

        Panel(accent = Sage) {
            Text("PRECOG reads", fontWeight = FontWeight.Medium, color = Sage)
            Spacer(Modifier.height(10.dp))
            Bullet("When a scroll happened, to the millisecond")
            Bullet("How far the list moved")
            Bullet("Which of your chosen apps you were in")
        }
        Spacer(Modifier.height(12.dp))
        Panel {
            Text("PRECOG cannot read", fontWeight = FontWeight.Medium)
            Spacer(Modifier.height(10.dp))
            Bullet("Anything on your screen — posts, messages, names, images")
            Bullet("What you type or tap")
            Bullet("Any app you did not pick")
            Spacer(Modifier.height(10.dp))
            Text(
                "Screen content is switched off in the service definition itself, so it never " +
                    "reaches the app. That is a setting Android enforces, not a policy PRECOG follows.",
                style = MaterialTheme.typography.bodySmall,
                color = TextSecondary,
            )
        }
        Spacer(Modifier.height(12.dp))
        Panel {
            Text("Where it goes", fontWeight = FontWeight.Medium)
            Spacer(Modifier.height(10.dp))
            Bullet("Nowhere. No account, no server, no network permission")
            Bullet("Stored encrypted on this phone, with a key held in secure hardware")
            Bullet("Raw timings are deleted after 48 hours; only the summary survives")
            Bullet("Delete everything at any time from Settings")
        }
    }
}

@Composable
private fun StepSetup(monitored: Set<String>, vm: PrecogViewModel) {
    Column {
        SectionLabel("Step 1 — choose apps")
        Spacer(Modifier.height(8.dp))
        Text("Which apps should PRECOG watch?", style = MaterialTheme.typography.titleLarge)
        Spacer(Modifier.height(16.dp))

        SettingsStore.CATALOGUE.forEach { app ->
            AppToggleRow(
                label = app.label,
                note = app.note,
                selected = app.pkg in monitored,
                onToggle = { vm.toggleApp(app.pkg) },
            )
            Spacer(Modifier.height(8.dp))
        }

        Spacer(Modifier.height(12.dp))
        Text(
            "YouTube is not on this list. Its feed draws through a surface Android's " +
                "accessibility layer cannot see, so PRECOG would record nothing there.",
            style = MaterialTheme.typography.bodySmall,
            color = TextSecondary,
        )

        Spacer(Modifier.height(28.dp))
        SectionLabel("Step 2 — turn on the reader")
        Spacer(Modifier.height(8.dp))
        Text(
            "Android puts this behind an accessibility permission. Find PRECOG in the list, " +
                "open it, and switch it on.",
            style = MaterialTheme.typography.bodyMedium,
            color = TextSecondary,
        )
    }
}

@Composable
private fun AppToggleRow(label: String, note: String, selected: Boolean, onToggle: () -> Unit) {
    Row(
        Modifier
            .fillMaxWidth()
            .clip(RoundedCornerShape(12.dp))
            .background(if (selected) Surface2 else androidx.compose.ui.graphics.Color.Transparent)
            .clickable(onClick = onToggle)
            .padding(14.dp),
        verticalAlignment = Alignment.CenterVertically,
    ) {
        Box(
            Modifier
                .size(20.dp)
                .clip(RoundedCornerShape(6.dp))
                .background(if (selected) Accent else Outline),
            contentAlignment = Alignment.Center,
        ) {
            if (selected) {
                Icon(
                    Icons.Filled.Check,
                    contentDescription = null,
                    tint = MaterialTheme.colorScheme.onPrimary,
                    modifier = Modifier.size(14.dp),
                )
            }
        }
        Spacer(Modifier.width(14.dp))
        Column(Modifier.weight(1f)) {
            Text(label, style = MaterialTheme.typography.bodyLarge)
            Text(note, style = MaterialTheme.typography.bodySmall, color = TextSecondary)
        }
    }
}

@Composable
internal fun Bullet(text: String) {
    Row(Modifier.padding(vertical = 3.dp), verticalAlignment = Alignment.Top) {
        Text("·", color = TextSecondary, modifier = Modifier.width(14.dp))
        Text(text, style = MaterialTheme.typography.bodyMedium, color = TextSecondary)
    }
}
