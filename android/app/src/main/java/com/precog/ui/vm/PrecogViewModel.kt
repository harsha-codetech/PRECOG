package com.precog.ui.vm

import android.app.Application
import androidx.lifecycle.AndroidViewModel
import androidx.lifecycle.viewModelScope
import com.precog.PrecogApplication
import com.precog.data.db.BaselineCellEntity
import com.precog.data.db.FeatureWindowEntity
import com.precog.data.db.SessionEntity
import com.precog.engine.BehaviouralState
import com.precog.engine.CellBaseline
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.map
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch
import java.util.Calendar

class PrecogViewModel(app: Application) : AndroidViewModel(app) {

    private val repo = PrecogApplication.repository(app)

    val consentGranted: StateFlow<Boolean> = repo.settings.consentGranted.stateOf(false)
    val onboardingComplete: StateFlow<Boolean?> =
        repo.settings.onboardingComplete.map { it as Boolean? }.stateOf(null)
    val monitoredApps: StateFlow<Set<String>> = repo.settings.monitoredApps.stateOf(emptySet())
    val pausedUntilMs: StateFlow<Long> = repo.settings.pausedUntilMs.stateOf(0L)

    val sessions: StateFlow<List<SessionEntity>> = repo.recentSessions(100).stateOf(emptyList())
    val todaySessions: StateFlow<List<SessionEntity>> = repo.sessionsSince(startOfToday()).stateOf(emptyList())
    val windowCount: StateFlow<Int> = repo.windowCount().stateOf(0)
    val baselineCells: StateFlow<List<BaselineCellEntity>> = repo.baselineCells().stateOf(emptyList())

    /** The state shown on the home screen: the most recent session that was actually scored. */
    val currentState: StateFlow<BehaviouralState> = repo.recentSessions(20)
        .map { list ->
            list.firstOrNull { it.stateOrdinal != null }
                ?.let { BehaviouralState.fromOrdinal(it.stateOrdinal) }
                ?: BehaviouralState.LEARNING
        }
        .stateOf(BehaviouralState.LEARNING)

    val latestScored: StateFlow<SessionEntity?> = repo.recentSessions(20)
        .map { list -> list.firstOrNull { it.stateOrdinal != null } }
        .stateOf(null)

    fun session(id: Long) = repo.session(id)

    suspend fun windowsFor(id: Long): List<FeatureWindowEntity> = repo.windowsForSession(id)

    /** The fitted model for one context cell, decoded on demand rather than held in memory. */
    suspend fun baselineFor(cellKey: String): CellBaseline? = repo.baselines.baselineFor(cellKey)

    fun grantConsent() = viewModelScope.launch { repo.settings.setConsent(true) }.let { }

    fun completeOnboarding() = viewModelScope.launch { repo.settings.setOnboardingComplete(true) }.let { }

    fun toggleApp(pkg: String) = viewModelScope.launch {
        val current = repo.settings.currentMonitoredApps()
        repo.settings.setMonitoredApps(if (pkg in current) current - pkg else current + pkg)
    }.let { }

    fun pauseFor(hours: Int) = viewModelScope.launch {
        repo.settings.pauseFor(hours * 60L * 60L * 1000L)
    }.let { }

    fun resume() = viewModelScope.launch { repo.settings.resume() }.let { }

    fun recordFeedback(sessionId: Long, agreed: Boolean) = viewModelScope.launch {
        repo.setFeedback(sessionId, if (agreed) 1 else 0)
    }.let { }

    fun deleteEverything() = viewModelScope.launch {
        repo.wipeEverything(getApplication())
    }.let { }

    private fun <T> kotlinx.coroutines.flow.Flow<T>.stateOf(initial: T): StateFlow<T> =
        stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), initial)

    private fun startOfToday(): Long = Calendar.getInstance().apply {
        set(Calendar.HOUR_OF_DAY, 0)
        set(Calendar.MINUTE, 0)
        set(Calendar.SECOND, 0)
        set(Calendar.MILLISECOND, 0)
    }.timeInMillis
}
