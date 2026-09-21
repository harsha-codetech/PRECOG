package com.precog.engine.math

import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.PI
import kotlin.math.exp
import kotlin.math.ln
import kotlin.random.Random

/**
 * Two-component Gaussian mixture with diagonal covariance (SPEC tier 2).
 *
 * Diagonal rather than full covariance throughout: per-cell counts on a phone are small
 * (the SPEC calls for diag/tied below n = 60 and cells rarely exceed that here), and a
 * full 6x6 covariance estimated from ~30 windows is not a model, it is noise.
 *
 * A negative log-likelihood is turned into a comparable deviation figure by calibrating
 * against the spread of training log-likelihoods, so it can sit alongside the PCA score.
 */
class DiagGmm(
    private val weights: DoubleArray,
    private val means: Array<DoubleArray>,
    private val variances: Array<DoubleArray>,
    private val nllCentre: Double,
    private val nllScale: Double,
) {
    val components: Int get() = weights.size

    fun logLikelihood(x: DoubleArray): Double {
        var maxTerm = Double.NEGATIVE_INFINITY
        val terms = DoubleArray(weights.size)
        for (c in weights.indices) {
            var acc = ln(weights[c].coerceAtLeast(1e-12))
            for (j in x.indices) {
                val v = variances[c][j]
                val diff = x[j] - means[c][j]
                acc += -0.5 * (ln(2.0 * PI * v) + diff * diff / v)
            }
            terms[c] = acc
            if (acc > maxTerm) maxTerm = acc
        }
        var sum = 0.0
        for (t in terms) sum += exp(t - maxTerm)
        return maxTerm + ln(sum)
    }

    /** Negative log-likelihood in robust sigma units of the training spread. */
    fun deviationSigma(x: DoubleArray): Double =
        Stats.robustZ(-logLikelihood(x), nllCentre, nllScale)

    fun toJson(): JSONObject = JSONObject().apply {
        put("weights", weights.toJsonArray())
        put("means", JSONArray().also { a -> means.forEach { a.put(it.toJsonArray()) } })
        put("variances", JSONArray().also { a -> variances.forEach { a.put(it.toJsonArray()) } })
        put("nllCentre", nllCentre)
        put("nllScale", nllScale)
    }

    companion object {
        private const val EM_ITERATIONS = 80
        private const val VARIANCE_FLOOR = 1e-4

        fun fit(rows: List<DoubleArray>, k: Int = 2, seed: Int = 7): DiagGmm {
            val n = rows.size
            val d = rows.first().size
            val rng = Random(seed)

            // Standardising the fit space keeps the variance floor meaningful across features.
            val centre = DoubleArray(d) { j -> Stats.median(Stats.column(rows, j)) }
            val scale = DoubleArray(d) { j -> Stats.madSigma(Stats.column(rows, j)) }
            val data = rows.map { r -> DoubleArray(d) { (r[it] - centre[it]) / scale[it] } }

            val effectiveK = k.coerceAtMost(n)
            val means = Array(effectiveK) { data[rng.nextInt(n)].copyOf() }
            // Nudge duplicate seeds apart so EM does not start degenerate.
            for (c in means.indices) for (j in 0 until d) means[c][j] += (rng.nextDouble() - 0.5) * 0.1
            val variances = Array(effectiveK) { DoubleArray(d) { 1.0 } }
            val weights = DoubleArray(effectiveK) { 1.0 / effectiveK }
            val resp = Array(n) { DoubleArray(effectiveK) }

            repeat(EM_ITERATIONS) {
                // E step
                for (i in 0 until n) {
                    var maxTerm = Double.NEGATIVE_INFINITY
                    for (c in 0 until effectiveK) {
                        var acc = ln(weights[c].coerceAtLeast(1e-12))
                        for (j in 0 until d) {
                            val v = variances[c][j]
                            val diff = data[i][j] - means[c][j]
                            acc += -0.5 * (ln(2.0 * PI * v) + diff * diff / v)
                        }
                        resp[i][c] = acc
                        if (acc > maxTerm) maxTerm = acc
                    }
                    var sum = 0.0
                    for (c in 0 until effectiveK) {
                        resp[i][c] = exp(resp[i][c] - maxTerm)
                        sum += resp[i][c]
                    }
                    for (c in 0 until effectiveK) resp[i][c] /= sum
                }
                // M step
                for (c in 0 until effectiveK) {
                    var nc = 0.0
                    for (i in 0 until n) nc += resp[i][c]
                    nc = nc.coerceAtLeast(1e-8)
                    weights[c] = nc / n
                    for (j in 0 until d) {
                        var m = 0.0
                        for (i in 0 until n) m += resp[i][c] * data[i][j]
                        means[c][j] = m / nc
                    }
                    for (j in 0 until d) {
                        var v = 0.0
                        for (i in 0 until n) {
                            val diff = data[i][j] - means[c][j]
                            v += resp[i][c] * diff * diff
                        }
                        variances[c][j] = (v / nc).coerceAtLeast(VARIANCE_FLOOR)
                    }
                }
            }

            // Fold the standardisation back into the parameters so logLikelihood takes raw vectors.
            val rawMeans = Array(effectiveK) { c -> DoubleArray(d) { means[c][it] * scale[it] + centre[it] } }
            val rawVars = Array(effectiveK) { c -> DoubleArray(d) { variances[c][it] * scale[it] * scale[it] } }

            val uncalibrated = DiagGmm(weights, rawMeans, rawVars, 0.0, 1.0)
            val nll = DoubleArray(n) { -uncalibrated.logLikelihood(rows[it]) }
            return DiagGmm(
                weights, rawMeans, rawVars,
                nllCentre = Stats.median(nll),
                nllScale = Stats.madSigma(nll),
            )
        }

        fun fromJson(o: JSONObject): DiagGmm {
            val means = o.getJSONArray("means")
            val vars = o.getJSONArray("variances")
            return DiagGmm(
                weights = o.getJSONArray("weights").toDoubleArray(),
                means = Array(means.length()) { means.getJSONArray(it).toDoubleArray() },
                variances = Array(vars.length()) { vars.getJSONArray(it).toDoubleArray() },
                nllCentre = o.getDouble("nllCentre"),
                nllScale = o.getDouble("nllScale"),
            )
        }
    }
}
