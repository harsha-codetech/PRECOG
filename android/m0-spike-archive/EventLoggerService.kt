package com.precog.m0spike

import android.accessibilityservice.AccessibilityService
import android.accessibilityservice.AccessibilityServiceInfo
import android.content.Context
import android.os.Environment
import android.util.Log
import android.view.accessibility.AccessibilityEvent
import java.io.File
import java.io.FileWriter
import java.io.IOException
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.ArrayBlockingQueue
import java.util.concurrent.Executors

/**
 * M0 Feasibility Spike — throwaway AccessibilityService.
 *
 * Purpose: determine which AccessibilityEvent fields are non-null for
 * TYPE_VIEW_SCROLLED events from Instagram, YouTube, TikTok, Reddit, and X.
 * Output: CSV written to external storage for offline inspection.
 *
 * This service collects NO content, NO text, NO view IDs beyond what is
 * needed to confirm which timing/delta fields are available. Discard after M0.
 *
 * Fields logged per event:
 *   ts_ms, package, event_type_name,
 *   scroll_delta_x, scroll_delta_y,
 *   from_index, to_index, item_count,
 *   max_scroll_x, max_scroll_y, scroll_x, scroll_y
 *
 * All boolean availability flags are logged so we can see which apps expose
 * which fields — this is the M0 question.
 */
class EventLoggerService : AccessibilityService() {

    companion object {
        private const val TAG = "PRECOG_M0"
        const val CSV_FILENAME = "precog_m0_events.csv"
        private const val QUEUE_CAPACITY = 4096

        // Target apps: the five platforms listed in SPEC §3
        private val TARGET_PACKAGES = setOf(
            "com.instagram.android",
            "com.google.android.youtube",
            "com.zhiliaoapp.musically",   // TikTok
            "com.reddit.frontpage",
            "com.twitter.android",        // X
        )

        // All event type names we want to see
        private val WATCH_TYPES = intArrayOf(
            AccessibilityEvent.TYPE_VIEW_SCROLLED,
            AccessibilityEvent.TYPE_VIEW_CLICKED,
            AccessibilityEvent.TYPE_WINDOW_STATE_CHANGED,
        )

        val CSV_HEADER = "ts_ms,package,event_type,scroll_delta_x,scroll_delta_y," +
            "from_index,to_index,item_count,max_scroll_x,max_scroll_y,scroll_x,scroll_y\n"
    }

    // Background thread pool: one thread for disk I/O so we never block the accessibility thread
    private val ioExecutor = Executors.newSingleThreadExecutor()
    private val queue = ArrayBlockingQueue<String>(QUEUE_CAPACITY)

    private lateinit var writer: FileWriter
    private var writerOpen = false

    // ── Lifecycle ───────────────────────────────────────────────────────────

    override fun onServiceConnected() {
        super.onServiceConnected()
        val info = serviceInfo ?: AccessibilityServiceInfo()
        info.apply {
            eventTypes = WATCH_TYPES.fold(0) { acc, t -> acc or t }
            feedbackType = AccessibilityServiceInfo.FEEDBACK_GENERIC
            notificationTimeout = 50L
            packageNames = TARGET_PACKAGES.toTypedArray()
            flags = AccessibilityServiceInfo.FLAG_REPORT_VIEW_IDS
        }
        serviceInfo = info

        openWriter()
        startFlushLoop()
        Log.i(TAG, "M0 spike connected — watching ${TARGET_PACKAGES.size} packages")
    }

    override fun onInterrupt() {
        Log.w(TAG, "M0 spike interrupted")
    }

    override fun onDestroy() {
        super.onDestroy()
        ioExecutor.submit { flushAndClose() }
        ioExecutor.shutdown()
        Log.i(TAG, "M0 spike destroyed")
    }

    // ── Event handling ───────────────────────────────────────────────────────

    override fun onAccessibilityEvent(event: AccessibilityEvent?) {
        event ?: return
        val pkg = event.packageName?.toString() ?: return
        if (pkg !in TARGET_PACKAGES) return

        val row = buildRow(event)
        if (!queue.offer(row)) {
            Log.w(TAG, "Queue full — dropping event")
        }
    }

    private fun buildRow(event: AccessibilityEvent): String {
        val ts = System.currentTimeMillis()
        val typeName = AccessibilityEvent.eventTypeToString(event.eventType)
        val pkg = event.packageName?.toString() ?: ""

        // scrollDeltaX / scrollDeltaY available API 28+; safe to call unconditionally on modern devices
        val sdx = event.scrollDeltaX
        val sdy = event.scrollDeltaY
        val fromIdx = event.fromIndex
        val toIdx = event.toIndex
        val itemCnt = event.itemCount
        val maxSx = event.maxScrollX
        val maxSy = event.maxScrollY
        val sx = event.scrollX
        val sy = event.scrollY

        return "$ts,$pkg,$typeName,$sdx,$sdy,$fromIdx,$toIdx,$itemCnt,$maxSx,$maxSy,$sx,$sy\n"
    }

    // ── Disk I/O (background thread) ─────────────────────────────────────────

    private fun openWriter() {
        ioExecutor.submit {
            try {
                val dir = getExternalFilesDir(null) ?: filesDir
                val file = File(dir, CSV_FILENAME)
                val needsHeader = !file.exists() || file.length() == 0L
                writer = FileWriter(file, true)
                if (needsHeader) writer.write(CSV_HEADER)
                writer.flush()
                writerOpen = true
                Log.i(TAG, "CSV open: ${file.absolutePath}")
            } catch (e: IOException) {
                Log.e(TAG, "Failed to open CSV", e)
            }
        }
    }

    private fun startFlushLoop() {
        ioExecutor.submit {
            while (!ioExecutor.isShutdown) {
                try {
                    val row = queue.take()  // blocks until available
                    if (!writerOpen) continue
                    writer.write(row)
                    // Flush every 50 rows to limit data loss risk without hammering storage
                    if (queue.isEmpty()) writer.flush()
                } catch (e: InterruptedException) {
                    Thread.currentThread().interrupt()
                    break
                } catch (e: IOException) {
                    Log.e(TAG, "Write error", e)
                }
            }
        }
    }

    private fun flushAndClose() {
        if (!writerOpen) return
        try {
            val remaining = mutableListOf<String>()
            queue.drainTo(remaining)
            remaining.forEach { writer.write(it) }
            writer.flush()
            writer.close()
            writerOpen = false
        } catch (e: IOException) {
            Log.e(TAG, "Close error", e)
        }
    }
}
