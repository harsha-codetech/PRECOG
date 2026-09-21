package com.precog.data

import android.content.Context
import androidx.datastore.preferences.core.booleanPreferencesKey
import androidx.datastore.preferences.core.edit
import androidx.datastore.preferences.core.longPreferencesKey
import androidx.datastore.preferences.core.stringSetPreferencesKey
import androidx.datastore.preferences.preferencesDataStore
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.first
import kotlinx.coroutines.flow.map

private val Context.dataStore by preferencesDataStore("precog_settings")

/** A monitorable app, with the capture caveat M0 established for it. */
data class MonitorableApp(
    val pkg: String,
    val label: String,
    val note: String,
)

class SettingsStore(private val context: Context) {

    private val consentKey = booleanPreferencesKey("consent_granted")
    private val onboardedKey = booleanPreferencesKey("onboarding_complete")
    private val appsKey = stringSetPreferencesKey("monitored_apps")
    private val pausedKey = longPreferencesKey("paused_until_ms")

    val consentGranted: Flow<Boolean> = context.dataStore.data.map { it[consentKey] ?: false }
    val onboardingComplete: Flow<Boolean> = context.dataStore.data.map { it[onboardedKey] ?: false }
    val monitoredApps: Flow<Set<String>> = context.dataStore.data.map { it[appsKey] ?: DEFAULT_APPS }
    val pausedUntilMs: Flow<Long> = context.dataStore.data.map { it[pausedKey] ?: 0L }

    suspend fun currentMonitoredApps(): Set<String> = monitoredApps.first()

    suspend fun isPaused(): Boolean = pausedUntilMs.first() > System.currentTimeMillis()

    suspend fun setConsent(granted: Boolean) =
        context.dataStore.edit { it[consentKey] = granted }.let { }

    suspend fun setOnboardingComplete(done: Boolean) =
        context.dataStore.edit { it[onboardedKey] = done }.let { }

    suspend fun setMonitoredApps(apps: Set<String>) =
        context.dataStore.edit { it[appsKey] = apps }.let { }

    suspend fun pauseFor(durationMs: Long) =
        context.dataStore.edit { it[pausedKey] = System.currentTimeMillis() + durationMs }.let { }

    suspend fun resume() = context.dataStore.edit { it[pausedKey] = 0L }.let { }

    suspend fun clearAll() = context.dataStore.edit { it.clear() }.let { }

    companion object {
        /**
         * The capture targets. YouTube is deliberately absent: the M0 feasibility spike
         * recorded 7 events and zero TYPE_VIEW_SCROLLED from it, because its feed renders
         * through a SurfaceView the accessibility layer cannot see. Listing it would promise
         * a signal that does not exist.
         */
        val CATALOGUE = listOf(
            MonitorableApp("com.instagram.android", "Instagram", "Swipe distance available; scroll position is not."),
            MonitorableApp("com.reddit.frontpage", "Reddit", "Scroll position available; swipe distance is not."),
            MonitorableApp("com.twitter.android", "X", "Both signals available."),
            MonitorableApp("com.snapchat.android", "Snapchat", "Untested — capture may be partial."),
            MonitorableApp("com.facebook.katana", "Facebook", "Untested — capture may be partial."),
            MonitorableApp("in.mohalla.sharechat", "ShareChat", "Untested — capture may be partial."),
        )

        val DEFAULT_APPS = setOf(
            "com.instagram.android",
            "com.reddit.frontpage",
            "com.twitter.android",
        )

        fun labelFor(pkg: String): String =
            CATALOGUE.firstOrNull { it.pkg == pkg }?.label ?: pkg.substringAfterLast('.')
    }
}
