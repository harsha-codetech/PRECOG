package com.precog.features

import com.precog.engine.math.Stats
import kotlin.math.abs
import kotlin.math.ln
import kotlin.math.sign

/** A raw scroll observation as the capture service resolves it. */
data class RawScroll(val tsMs: Long, val delta: Int?)

/**
 * Turns a session's raw scroll events into feature windows.
 *
 * A window is [WINDOW_SIZE] consecutive scroll events. Windows do not overlap, so each
 * contributes independent evidence to the baseline. A trailing partial window is kept when
 * it holds at least [MIN_WINDOW] events, because short sessions are exactly the ones a
 * distraction signal needs to catch.
 */
object FeatureExtractor {

    const val WINDOW_SIZE = 20
    const val MIN_WINDOW = 12

    /** Gaps shorter than this count as uninterrupted consumption rather than deliberate pacing. */
    private const val UNBROKEN_GAP_MS = 400.0

    /** A gap longer than this is the user doing something else; it should not skew the rhythm. */
    private const val GAP_CEILING_MS = 10_000.0

    fun windows(events: List<RawScroll>): List<FeatureVector> {
        if (events.size < MIN_WINDOW) return emptyList()
        val sorted = events.sortedBy { it.tsMs }
        val out = ArrayList<FeatureVector>()
        var i = 0
        while (i + MIN_WINDOW <= sorted.size) {
            val end = minOf(i + WINDOW_SIZE, sorted.size)
            out += extract(sorted.subList(i, end))
            i = end
        }
        return out
    }

    fun extract(window: List<RawScroll>): FeatureVector {
        val n = window.size
        val gaps = DoubleArray(n - 1) {
            (window[it + 1].tsMs - window[it].tsMs).toDouble().coerceIn(1.0, GAP_CEILING_MS)
        }

        val medianGap = Stats.median(gaps).coerceAtLeast(1.0)
        // Robust coefficient of variation. A metronomic scroll sits near zero; a stop-start
        // reading rhythm sits high. This is the burstiness term from the offline work.
        val burstiness = Stats.madSigma(gaps) / medianGap

        val unbrokenRatio = gaps.count { it < UNBROKEN_GAP_MS }.toDouble() / gaps.size

        // Direction reversals. M0 found scrollDeltaY is a constant -1 sentinel on some apps,
        // so the capture layer resolves delta per app before it reaches here; an unresolved
        // delta contributes no direction information rather than a fake zero.
        val directions = window.mapNotNull { it.delta }.filter { it != 0 }.map { sign(it.toDouble()) }
        val reversals = if (directions.size < 2) 0
            else (1 until directions.size).count { directions[it] != directions[it - 1] }
        val reversalRate = if (directions.size < 2) 0.0 else reversals.toDouble() / (directions.size - 1)

        val magnitudes = window.mapNotNull { it.delta }.map { abs(it).toDouble() }.filter { it > 0 }
        val deltaMag = if (magnitudes.isEmpty()) 0.0 else Stats.median(magnitudes.toDoubleArray())

        val spanMs = (window.last().tsMs - window.first().tsMs).coerceAtLeast(1L).toDouble()
        val eventRate = n * 1000.0 / spanMs

        return FeatureVector(
            doubleArrayOf(
                ln(medianGap),
                burstiness,
                unbrokenRatio,
                reversalRate,
                ln(1.0 + deltaMag),
                eventRate,
            )
        )
    }
}
