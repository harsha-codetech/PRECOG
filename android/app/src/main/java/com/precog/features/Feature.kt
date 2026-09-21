package com.precog.features

import java.util.Calendar
import kotlin.math.abs
import kotlin.math.exp

/**
 * The six features PRECOG can actually observe through an AccessibilityService.
 *
 * The offline study used 28 Touchalytics kinematic features. None of those transfer: a
 * third-party Android app cannot see raw MotionEvent coordinates, pressure, or trajectory.
 * What survives is event timing plus a coarse scroll magnitude. That is a real and
 * documented reduction in signal, not an equivalent substitution.
 *
 * **The unit is the scroll event, not the swipe.** Measured on device 2026-09-21: ten deliberate
 * swipes, each with a clear pause, produced **54 TYPE_VIEW_SCROLLED events** — Android reports
 * repeatedly while a fling decelerates. Every feature here is therefore computed over scroll
 * steps, and the user-facing wording says "step", not "swipe". MEDIAN_GAP in particular is
 * dominated by intra-fling spacing rather than by how long a person pauses between swipes; it is
 * not a measure of human pacing and must not be described as one.
 *
 * [plainRise] and [plainFall] are the user-facing wording. The UI never shows bare sigma
 * figures as its primary reading — an evaluation finding (F-07): sigma units are meaningless
 * to a general audience.
 */
enum class Feature(
    val index: Int,
    val label: String,
    val plainRise: String,
    val plainFall: String,
    /** Feature space is log-scaled, so a difference can be reported as a ratio. */
    val isLog: Boolean,
) {
    MEDIAN_GAP(0, "Gap between scroll steps", "leaving longer gaps between scroll steps", "leaving shorter gaps", true),
    BURSTINESS(1, "Rhythm steadiness", "scrolling in more uneven bursts", "scrolling more mechanically", false),
    /**
     * Fraction of inter-event gaps below 400 ms.
     *
     * Renamed from PASSIVE_RATIO on 2026-09-20. `SPEC.md` §4 defines `passive_ratio` as
     * *windows containing scrolls and zero clicks, over all windows* — a different quantity
     * measured from different events. Two names for two things; do not reunify them.
     */
    UNBROKEN_RATIO(2, "Unbroken scrolling", "scrolling for longer without stopping", "stopping more often", false),
    REVERSAL_RATE(3, "Backtracking", "scrolling back up more often", "scrolling back up less", false),
    DELTA_MAGNITUDE(4, "Scroll step size", "moving further per scroll step", "moving less per scroll step", true),
    EVENT_RATE(5, "Scroll speed", "scrolling faster", "scrolling slower", false);

    companion object {
        val DIMENSIONS = entries.size
        fun at(i: Int) = entries[i]
    }
}

/** One window's feature vector, in the order the [Feature] indices declare. */
@JvmInline
value class FeatureVector(val values: DoubleArray) {
    operator fun get(f: Feature): Double = values[f.index]
}

/** A single ranked piece of evidence behind a state call. */
data class FeatureEvidence(
    val feature: Feature,
    val sigma: Double,
    val observed: Double,
    val usual: Double,
) {
    /** "scrolling faster than usual" style wording, with no sigma in it. */
    val plainDirection: String get() = if (sigma >= 0) feature.plainRise else feature.plainFall

    val intensity: String get() = when (abs(sigma)) {
        in 0.0..1.0 -> "within your usual range"
        in 1.0..2.0 -> "slightly"
        in 2.0..3.0 -> "noticeably"
        else -> "far"
    }

    /**
     * A concrete comparison instead of a sigma figure — "about 2.4x shorter pauses".
     * Returns null when a ratio would not be meaningful (a rate already near zero).
     */
    val plainMagnitude: String? get() {
        if (abs(sigma) < 1.0) return null
        return if (feature.isLog) {
            val ratio = exp(abs(observed - usual))
            if (ratio < 1.15) null
            else String.format("about %.1fx %s than usual", ratio, if (observed > usual) "longer" else "shorter")
        } else {
            if (usual < 1e-3) null
            else {
                val ratio = observed / usual
                if (ratio in 0.85..1.15) null
                else String.format("about %.0f%% %s than usual", abs(ratio - 1.0) * 100, if (ratio > 1) "higher" else "lower")
            }
        }
    }
}

/** Context cell: the same person scrolls differently at 8am and at midnight, and per app. */
object ContextCell {

    val BUCKET_LABELS = arrayOf("Morning", "Afternoon", "Evening", "Night")

    fun bucketOf(tsMs: Long): Int {
        val cal = Calendar.getInstance().apply { timeInMillis = tsMs }
        return when (cal.get(Calendar.HOUR_OF_DAY)) {
            in 6..11 -> 0
            in 12..16 -> 1
            in 17..21 -> 2
            else -> 3
        }
    }

    fun key(pkg: String, bucket: Int) = "$pkg|$bucket"

    fun bucketLabel(bucket: Int) = BUCKET_LABELS.getOrElse(bucket) { "Unknown" }
}
