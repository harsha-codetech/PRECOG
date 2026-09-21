package com.precog.engine

import com.precog.engine.math.DiagGmm
import com.precog.engine.math.Pca
import com.precog.engine.math.Stats
import com.precog.engine.math.toDoubleArray
import com.precog.engine.math.toJsonArray
import com.precog.features.Feature
import com.precog.features.FeatureEvidence
import com.precog.features.FeatureVector
import org.json.JSONObject
import kotlin.math.abs

/** A fitted baseline for one context cell, with everything needed to score and to explain. */
class CellBaseline(
    val cellKey: String,
    val n: Int,
    /** Per-feature centre, after empirical-Bayes shrinkage toward the cross-cell centre. */
    val centres: DoubleArray,
    val scales: DoubleArray,
    val pca: Pca,
    val gmm: DiagGmm,
) {

    /** How much this baseline can be trusted: sample size x how tight the pattern is. */
    val confidence: Double by lazy {
        val nFactor = (n.toDouble() / CONFIDENCE_SATURATION_N).coerceAtMost(1.0)
        val relativeSpread = Stats.median(
            DoubleArray(centres.size) { scales[it] / (abs(centres[it]) + 1.0) }
        )
        val tightness = 1.0 / (1.0 + 3.0 * relativeSpread)
        (nFactor * tightness).coerceIn(0.0, 1.0)
    }

    fun evidence(x: FeatureVector): List<FeatureEvidence> =
        Feature.entries.map { f ->
            FeatureEvidence(
                feature = f,
                sigma = Stats.robustZ(x.values[f.index], centres[f.index], scales[f.index]),
                observed = x.values[f.index],
                usual = centres[f.index],
            )
        }.sortedByDescending { abs(it.sigma) }

    fun score(x: FeatureVector): DeviationResult {
        val pcaSigma = pca.deviationSigma(x.values)
        val gmmSigma = gmm.deviationSigma(x.values)
        // Either detector firing is enough. Both are calibrated in robust sigma units of
        // their own training spread, so the max is comparable across cells.
        val combined = maxOf(pcaSigma, gmmSigma).coerceAtLeast(0.0)
        val ev = evidence(x)
        return DeviationResult(
            score = combined,
            state = StateClassifier.classify(combined, confidence, ev),
            confidence = confidence,
            evidence = ev,
            pcaSigma = pcaSigma,
            gmmSigma = gmmSigma,
        )
    }

    fun toJson(): JSONObject = JSONObject().apply {
        put("n", n)
        put("centres", centres.toJsonArray())
        put("scales", scales.toJsonArray())
        put("pca", pca.toJson())
        put("gmm", gmm.toJson())
    }

    companion object {
        /** Sample size at which the count term stops holding confidence back. */
        const val CONFIDENCE_SATURATION_N = 60

        fun fromJson(cellKey: String, o: JSONObject) = CellBaseline(
            cellKey = cellKey,
            n = o.getInt("n"),
            centres = o.getJSONArray("centres").toDoubleArray(),
            scales = o.getJSONArray("scales").toDoubleArray(),
            pca = Pca.fromJson(o.getJSONObject("pca")),
            gmm = DiagGmm.fromJson(o.getJSONObject("gmm")),
        )
    }
}
