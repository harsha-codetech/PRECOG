package com.precog.service

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.os.Build
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import com.precog.PrecogApplication
import com.precog.features.RawScroll
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.delay
import kotlinx.coroutines.launch
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock

/**
 * Reads scroll event timing from the apps the user selected.
 *
 * What it can see: when a scroll happened, and how far the list moved. What it cannot see,
 * by configuration rather than by promise: window content. `canRetrieveWindowContent` is
 * false in the service config, so no text, no labels, and no tapped values ever reach this
 * process. The privacy claim is enforced at the capture boundary, not in policy.
 *
 * The callback thread never touches disk. Events land in an in-memory buffer; a coroutine
 * closes the session and hands it to the repository once scrolling stops.
 */
class ScrollCaptureService : AccessibilityService() {

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.IO)
    private val bufferLock = Mutex()

    private var buffer = ArrayList<RawScroll>(BUFFER_HINT)
    private var currentPkg: String? = null
    private var lastScrollY: Int? = null
    private var idleJob: Job? = null

    @Volatile private var monitored: Set<String> = emptySet()
    @Volatile private var paused: Boolean = false

    override fun onServiceConnected() {
        super.onServiceConnected()
        serviceInfo = AccessibilityServiceInfo().apply {
            eventTypes = AccessibilityEvent.TYPE_VIEW_SCROLLED or
                AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            notificationTimeout = 0
            flags = AccessibilityServiceInfo.DEFAULT
        }
        val repo = PrecogApplication.repository(this)
        scope.launch {
            repo.settings.monitoredApps.collect { monitored = it }
        }
        scope.launch {
            repo.settings.pausedUntilMs.collect { paused = it > System.currentTimeMillis() }
        }
        running = true
        Log.i(TAG, "capture connected")
    }

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        val e = event ?: return
        val pkg = e.packageName?.toString() ?: return
        if (paused) return

        if (e.eventType == AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED) {
            if (pkg != currentPkg) closeSession()
            return
        }
        if (e.eventType != AccessibilityEvent.TYPE_VIEW_SCROLLED) return
        if (pkg !in monitored) {
            if (currentPkg != null) closeSession()
            return
        }
        if (pkg != currentPkg) {
            closeSession()
            currentPkg = pkg
            lastScrollY = null
        }

        val ts = System.currentTimeMillis()
        val delta = resolveDelta(e)
        scope.launch {
            bufferLock.withLock { buffer.add(RawScroll(ts, delta)) }
        }
        armIdleTimer()
    }

    /**
     * Scroll magnitude, resolved per app because no single signal works everywhere.
     *
     * The M0 spike found scrollDeltaY carries real values on Instagram and X but is a
     * constant -1 sentinel on Reddit, while scrollY is the mirror image: it advances on
     * Reddit and X but stays fixed on Instagram. Preferring a non-sentinel delta and
     * falling back to differencing scrollY covers all three. When neither is usable the
     * result is null, and the extractor treats it as absent rather than as a zero — a
     * missing signal must not be laundered into a real-looking value.
     */
    private fun resolveDelta(e: AccessibilityEvent): Int? {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            val d = e.scrollDeltaY
            if (d != 0 && d != SENTINEL) return d
        }
        @Suppress("DEPRECATION")
        val y = e.scrollY
        if (y >= 0) {
            val previous = lastScrollY
            lastScrollY = y
            if (previous != null && previous != y) return y - previous
        }
        return null
    }

    private fun armIdleTimer() {
        idleJob?.cancel()
        idleJob = scope.launch {
            delay(SESSION_IDLE_MS)
            closeSession()
        }
    }

    /** Hands the buffered session to the repository and starts a fresh one. */
    private fun closeSession() {
        idleJob?.cancel()
        idleJob = null
        val pkg = currentPkg ?: return
        currentPkg = null
        lastScrollY = null
        val repo = PrecogApplication.repository(this)
        scope.launch {
            val events = bufferLock.withLock {
                val snapshot = buffer
                buffer = ArrayList(BUFFER_HINT)
                snapshot
            }
            if (events.isEmpty()) return@launch
            runCatching { repo.ingestSession(pkg, events) }
                .onFailure { Log.e(TAG, "ingest failed", it) }
        }
    }

    override fun onInterrupt() = closeSession()

    override fun onDestroy() {
        running = false
        closeSession()
        scope.cancel()
        super.onDestroy()
    }

    companion object {
        private const val TAG = "PRECOG"

        /** Reddit reports this constant instead of a real delta; see [resolveDelta]. */
        private const val SENTINEL = -1

        /** Scrolling that stops for this long ends the session. */
        private const val SESSION_IDLE_MS = 45_000L

        private const val BUFFER_HINT = 256

        @Volatile private var running = false

        /** Whether the accessibility service is currently connected. */
        fun isRunning() = running
    }
}
