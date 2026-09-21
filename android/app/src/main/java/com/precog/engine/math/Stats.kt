package com.precog.engine.math

import kotlin.math.abs
import kotlin.math.sqrt

/** Small robust-statistics helpers. All operate on plain DoubleArrays; no allocation drama. */
object Stats {

    /** Scale factor making MAD a consistent estimator of sigma under normality. */
    const val MAD_TO_SIGMA = 1.4826

    /** Floor applied to any scale estimate so a degenerate cell cannot divide by zero. */
    private const val SCALE_FLOOR = 1e-6

    fun mean(xs: DoubleArray): Double = if (xs.isEmpty()) 0.0 else xs.sum() / xs.size

    fun median(xs: DoubleArray): Double {
        if (xs.isEmpty()) return 0.0
        val s = xs.sortedArray()
        val m = s.size / 2
        return if (s.size % 2 == 1) s[m] else (s[m - 1] + s[m]) / 2.0
    }

    /** Median absolute deviation, scaled to sigma units. */
    fun madSigma(xs: DoubleArray): Double {
        if (xs.size < 2) return SCALE_FLOOR
        val med = median(xs)
        val dev = DoubleArray(xs.size) { abs(xs[it] - med) }
        return (median(dev) * MAD_TO_SIGMA).coerceAtLeast(SCALE_FLOOR)
    }

    fun sd(xs: DoubleArray): Double {
        if (xs.size < 2) return SCALE_FLOOR
        val m = mean(xs)
        var acc = 0.0
        for (x in xs) acc += (x - m) * (x - m)
        return sqrt(acc / (xs.size - 1)).coerceAtLeast(SCALE_FLOOR)
    }

    /**
     * Deviation of [x] from a centre in robust sigma units.
     * Signed: positive means above the user's usual value.
     */
    fun robustZ(x: Double, centre: Double, scaleSigma: Double): Double =
        (x - centre) / scaleSigma.coerceAtLeast(SCALE_FLOOR)

    fun percentile(xs: DoubleArray, p: Double): Double {
        if (xs.isEmpty()) return 0.0
        val s = xs.sortedArray()
        val idx = (p.coerceIn(0.0, 1.0) * (s.size - 1))
        val lo = idx.toInt()
        val hi = minOf(lo + 1, s.size - 1)
        val frac = idx - lo
        return s[lo] * (1 - frac) + s[hi] * frac
    }

    fun column(rows: List<DoubleArray>, j: Int): DoubleArray =
        DoubleArray(rows.size) { rows[it][j] }
}
