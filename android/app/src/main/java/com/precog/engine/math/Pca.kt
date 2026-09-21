package com.precog.engine.math

import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.sqrt

/**
 * PCA reconstruction-error detector (SPEC tier 3).
 *
 * Data is first put on a robust scale (median / MAD-sigma) so one heavy-tailed feature
 * cannot dominate the principal axes. The retained rank [k] is chosen by the 85%
 * cumulative-variance criterion rather than fixed: the offline study used k = 8 over 28
 * kinematic features, and this feature set has only six, so a fixed k would not carry over.
 */
class Pca(
    private val centre: DoubleArray,
    private val scale: DoubleArray,
    /** [k] rows, each a unit eigenvector of length d. */
    private val components: Array<DoubleArray>,
    private val errCentre: Double,
    private val errScale: Double,
    val k: Int,
    val explainedVariance: Double,
) {

    fun reconstructionError(x: DoubleArray): Double {
        val z = DoubleArray(x.size) { (x[it] - centre[it]) / scale[it] }
        val recon = DoubleArray(x.size)
        for (c in components) {
            var proj = 0.0
            for (j in z.indices) proj += z[j] * c[j]
            for (j in z.indices) recon[j] += proj * c[j]
        }
        var acc = 0.0
        for (j in z.indices) {
            val r = z[j] - recon[j]
            acc += r * r
        }
        return sqrt(acc)
    }

    /** Reconstruction error expressed in robust sigma units of the training error spread. */
    fun deviationSigma(x: DoubleArray): Double =
        Stats.robustZ(reconstructionError(x), errCentre, errScale)

    fun toJson(): JSONObject = JSONObject().apply {
        put("centre", centre.toJsonArray())
        put("scale", scale.toJsonArray())
        put("components", JSONArray().also { arr -> components.forEach { arr.put(it.toJsonArray()) } })
        put("errCentre", errCentre)
        put("errScale", errScale)
        put("k", k)
        put("explainedVariance", explainedVariance)
    }

    companion object {
        private const val VARIANCE_TARGET = 0.85

        fun fit(rows: List<DoubleArray>): Pca {
            val d = rows.first().size
            val centre = DoubleArray(d) { j -> Stats.median(Stats.column(rows, j)) }
            val scale = DoubleArray(d) { j -> Stats.madSigma(Stats.column(rows, j)) }
            val z = rows.map { r -> DoubleArray(d) { (r[it] - centre[it]) / scale[it] } }

            val eigen = Matrix.symmetricEigen(Matrix.covariance(z))
            val positive = eigen.values.map { it.coerceAtLeast(0.0) }
            val total = positive.sum().coerceAtLeast(1e-12)

            var cumulative = 0.0
            var k = 1
            for (i in positive.indices) {
                cumulative += positive[i]
                k = i + 1
                if (cumulative / total >= VARIANCE_TARGET) break
            }
            // Keeping every axis would make the residual identically zero and the detector blind.
            k = k.coerceIn(1, d - 1)
            val explained = positive.take(k).sum() / total

            val components = Array(k) { eigen.component(it) }
            val model = Pca(centre, scale, components, 0.0, 1.0, k, explained)
            val errs = DoubleArray(rows.size) { model.reconstructionError(rows[it]) }
            return Pca(
                centre, scale, components,
                errCentre = Stats.median(errs),
                errScale = Stats.madSigma(errs),
                k = k,
                explainedVariance = explained,
            )
        }

        fun fromJson(o: JSONObject): Pca {
            val comps = o.getJSONArray("components")
            return Pca(
                centre = o.getJSONArray("centre").toDoubleArray(),
                scale = o.getJSONArray("scale").toDoubleArray(),
                components = Array(comps.length()) { comps.getJSONArray(it).toDoubleArray() },
                errCentre = o.getDouble("errCentre"),
                errScale = o.getDouble("errScale"),
                k = o.getInt("k"),
                explainedVariance = o.getDouble("explainedVariance"),
            )
        }
    }
}

internal fun DoubleArray.toJsonArray(): JSONArray = JSONArray().also { a -> forEach { a.put(it) } }

internal fun JSONArray.toDoubleArray(): DoubleArray = DoubleArray(length()) { getDouble(it) }
