package com.precog.engine

import com.precog.data.db.BaselineCellEntity
import com.precog.data.db.FeatureWindowEntity
import com.precog.data.db.PrecogDatabase
import com.precog.engine.math.DiagGmm
import com.precog.engine.math.Pca
import com.precog.engine.math.Stats
import com.precog.features.Feature
import com.precog.features.FeatureVector
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import org.json.JSONObject
import java.util.concurrent.ConcurrentHashMap

/**
 * Fits and serves per-context-cell baselines.
 *
 * Cells are sparse by construction — a person uses a handful of apps at a handful of times
 * of day — so each cell's centre and scale are shrunk toward the cross-cell estimate with
 * empirical-Bayes weighting. A cell with 25 windows borrows heavily from the user's overall
 * pattern; a cell with 200 stands on its own. This is the part of the offline method that
 * transfers to the phone unchanged, because it is about sample size, not about features.
 */
class BaselineEngine(private val db: PrecogDatabase) {

    private val cache = ConcurrentHashMap<String, CellBaseline>()

    suspend fun baselineFor(cellKey: String): CellBaseline? {
        cache[cellKey]?.let { return it }
        val row = db.baselines().byKey(cellKey) ?: return null
        return runCatching { CellBaseline.fromJson(cellKey, JSONObject(row.modelJson)) }
            .getOrNull()
            ?.also { cache[cellKey] = it }
    }

    /** Refits every cell that has enough windows. Returns the number of cells fitted. */
    suspend fun rebuildAll(): Int = withContext(Dispatchers.Default) {
        val eligible = db.featureWindows().eligibleCells(MIN_CELL_WINDOWS)
        if (eligible.isEmpty()) return@withContext 0

        val pool = db.featureWindows().recent(GLOBAL_POOL_LIMIT).map { it.toVector().values }
        if (pool.size < MIN_CELL_WINDOWS) return@withContext 0

        val globalCentres = DoubleArray(Feature.DIMENSIONS) { j -> Stats.median(Stats.column(pool, j)) }
        val globalScales = DoubleArray(Feature.DIMENSIONS) { j -> Stats.madSigma(Stats.column(pool, j)) }

        var fitted = 0
        for (cellKey in eligible) {
            val rows = db.featureWindows().forCell(cellKey, CELL_FIT_LIMIT)
            if (rows.size < MIN_CELL_WINDOWS) continue
            val data = rows.map { it.toVector().values }
            val n = data.size

            // Empirical-Bayes weight: the cell's own estimate earns trust with sample size.
            val w = n.toDouble() / (n + SHRINKAGE_PRIOR_N)
            val centres = DoubleArray(Feature.DIMENSIONS) { j ->
                w * Stats.median(Stats.column(data, j)) + (1 - w) * globalCentres[j]
            }
            val scales = DoubleArray(Feature.DIMENSIONS) { j ->
                w * Stats.madSigma(Stats.column(data, j)) + (1 - w) * globalScales[j]
            }

            val baseline = runCatching {
                CellBaseline(
                    cellKey = cellKey,
                    n = n,
                    centres = centres,
                    scales = scales,
                    pca = Pca.fit(data),
                    gmm = DiagGmm.fit(data, k = GMM_COMPONENTS),
                )
            }.getOrNull() ?: continue

            val first = rows.first()
            db.baselines().upsert(
                BaselineCellEntity(
                    cellKey = cellKey,
                    pkg = first.pkg,
                    bucket = first.bucket,
                    n = n,
                    updatedMs = System.currentTimeMillis(),
                    modelJson = baseline.toJson().toString(),
                )
            )
            cache[cellKey] = baseline
            fitted++
        }
        fitted
    }

    fun invalidate() = cache.clear()

    companion object {
        /**
         * Windows a cell needs before it is modelled at all. Each window is 20 scroll events,
         * so this is roughly 500 events in one app at one time of day. The offline study's
         * n >= 80 figure was per kinematic gesture and does not carry over directly; this gate
         * is set by what a six-dimensional GMM and PCA actually need to be stable.
         */
        const val MIN_CELL_WINDOWS = 25

        const val GMM_COMPONENTS = 2
        private const val SHRINKAGE_PRIOR_N = 30
        private const val CELL_FIT_LIMIT = 400
        private const val GLOBAL_POOL_LIMIT = 2000
    }
}

fun FeatureWindowEntity.toVector() = FeatureVector(
    doubleArrayOf(logMedianGap, burstiness, unbrokenRatio, reversalRate, logDeltaMag, eventRate)
)
