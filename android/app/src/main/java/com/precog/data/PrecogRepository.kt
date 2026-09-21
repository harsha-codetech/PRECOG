package com.precog.data

import android.content.Context
import com.precog.data.db.FeatureWindowEntity
import com.precog.data.db.PrecogDatabase
import com.precog.data.db.ScrollEventEntity
import com.precog.data.db.SessionEntity
import com.precog.engine.BaselineEngine
import com.precog.engine.BehaviouralState
import com.precog.engine.CellBaseline
import com.precog.engine.DeviationResult
import com.precog.engine.StateClassifier
import com.precog.engine.math.Stats
import com.precog.features.ContextCell
import com.precog.features.Feature
import com.precog.features.FeatureEvidence
import com.precog.features.FeatureExtractor
import com.precog.features.FeatureVector
import com.precog.features.RawScroll
import kotlinx.coroutines.flow.Flow
import org.json.JSONArray
import org.json.JSONObject
import kotlin.math.abs

/** Everything the UI and the capture service talk to. One instance, held by the Application. */
class PrecogRepository(context: Context) {

    private val db = PrecogDatabase.get(context)
    val settings = SettingsStore(context)
    val baselines = BaselineEngine(db)

    fun recentSessions(limit: Int = 50): Flow<List<SessionEntity>> = db.sessions().recentFlow(limit)
    fun sessionsSince(sinceMs: Long): Flow<List<SessionEntity>> = db.sessions().sinceFlow(sinceMs)
    fun session(id: Long): Flow<SessionEntity?> = db.sessions().byIdFlow(id)
    fun windowCount(): Flow<Int> = db.featureWindows().totalFlow()
    fun sessionCount(): Flow<Int> = db.sessions().countFlow()
    fun baselineCells() = db.baselines().allFlow()

    suspend fun windowsForSession(id: Long) = db.featureWindows().forSession(id)
    suspend fun setFeedback(id: Long, feedback: Int) = db.sessions().setFeedback(id, feedback)
    suspend fun totalWindows() = db.featureWindows().total()

    /**
     * Closes out one capture session: persists the raw events, derives feature windows,
     * scores each against its cell baseline, aggregates to a session verdict, and refits
     * baselines. Called off the accessibility callback thread.
     */
    suspend fun ingestSession(pkg: String, events: List<RawScroll>) {
        if (events.size < FeatureExtractor.MIN_WINDOW) return

        db.scrollEvents().insertAll(
            events.map {
                ScrollEventEntity(tsMs = it.tsMs, pkg = pkg, delta = it.delta, deltaFromScrollY = false)
            }
        )
        db.scrollEvents().purgeBefore(System.currentTimeMillis() - RAW_RETENTION_MS)

        val vectors = FeatureExtractor.windows(events)
        if (vectors.isEmpty()) return

        val startMs = events.minOf { it.tsMs }
        val endMs = events.maxOf { it.tsMs }
        val bucket = ContextCell.bucketOf(startMs)
        val cellKey = ContextCell.key(pkg, bucket)

        val sessionId = db.sessions().insert(
            SessionEntity(
                pkg = pkg,
                startMs = startMs,
                endMs = endMs,
                eventCount = events.size,
                windowCount = vectors.size,
                bucket = bucket,
                peakScore = null,
                medianScore = null,
                stateOrdinal = null,
                confidence = 0.0,
                evidenceJson = null,
                feedback = null,
            )
        )

        val baseline = baselines.baselineFor(cellKey)
        val results = vectors.map { v -> baseline?.score(v) }

        db.featureWindows().insertAll(
            vectors.mapIndexed { i, v ->
                FeatureWindowEntity(
                    sessionId = sessionId,
                    tsMs = startMs + (endMs - startMs) * i / vectors.size.coerceAtLeast(1),
                    pkg = pkg,
                    bucket = bucket,
                    cellKey = cellKey,
                    logMedianGap = v.values[0],
                    burstiness = v.values[1],
                    unbrokenRatio = v.values[2],
                    reversalRate = v.values[3],
                    logDeltaMag = v.values[4],
                    eventRate = v.values[5],
                    score = results.getOrNull(i)?.score,
                    stateOrdinal = results.getOrNull(i)?.state?.ordinal,
                )
            }
        )

        if (baseline != null) {
            val scored = results.filterNotNull()
            val outcome = aggregate(baseline, vectors, scored)
            db.sessions().setOutcome(
                id = sessionId,
                peak = outcome.score,
                median = Stats.median(scored.map { it.score }.toDoubleArray()),
                state = outcome.state.ordinal,
                conf = outcome.confidence,
                evidence = evidenceToJson(outcome.evidence),
            )
        }

        baselines.rebuildAll()
    }

    /**
     * Session verdict from its windows. The state comes from the 80th percentile of window
     * scores rather than the maximum: one odd window inside an otherwise ordinary session is
     * noise, and alerting on it is how a tool like this loses the trust of the person using it.
     */
    private fun aggregate(
        baseline: CellBaseline,
        vectors: List<FeatureVector>,
        results: List<DeviationResult>,
    ): DeviationResult {
        if (results.isEmpty()) {
            return DeviationResult(0.0, BehaviouralState.LEARNING, baseline.confidence, emptyList(), 0.0, 0.0)
        }
        val scores = results.map { it.score }.toDoubleArray()
        val representative = Stats.percentile(scores, 0.80)

        // Evidence is averaged across windows so it describes the session, not one slice of it.
        val meanSigma = DoubleArray(Feature.DIMENSIONS)
        val meanObserved = DoubleArray(Feature.DIMENSIONS)
        for (r in results) for (e in r.evidence) meanSigma[e.feature.index] += e.sigma / results.size
        for (v in vectors) for (j in 0 until Feature.DIMENSIONS) meanObserved[j] += v.values[j] / vectors.size

        val evidence = Feature.entries.map { f ->
            FeatureEvidence(f, meanSigma[f.index], meanObserved[f.index], baseline.centres[f.index])
        }.sortedByDescending { abs(it.sigma) }

        return DeviationResult(
            score = representative,
            state = StateClassifier.classify(representative, baseline.confidence, evidence),
            confidence = baseline.confidence,
            evidence = evidence,
            pcaSigma = results.map { it.pcaSigma }.average(),
            gmmSigma = results.map { it.gmmSigma }.average(),
        )
    }

    suspend fun wipeEverything(context: Context) {
        settings.clearAll()
        baselines.invalidate()
        PrecogDatabase.wipe(context)
    }

    companion object {
        /**
         * Raw events are a working buffer, not an archive. They exist so a changed extractor
         * can be re-run over recent data; after this they are deleted and only the derived
         * feature vectors remain.
         */
        const val RAW_RETENTION_MS = 48L * 60 * 60 * 1000

        fun evidenceToJson(evidence: List<FeatureEvidence>): String = JSONArray().also { arr ->
            evidence.forEach { e ->
                arr.put(
                    JSONObject().apply {
                        put("f", e.feature.index)
                        put("sigma", e.sigma)
                        put("observed", e.observed)
                        put("usual", e.usual)
                    }
                )
            }
        }.toString()

        fun evidenceFromJson(json: String?): List<FeatureEvidence> {
            if (json.isNullOrBlank()) return emptyList()
            return runCatching {
                val arr = JSONArray(json)
                (0 until arr.length()).map { i ->
                    val o = arr.getJSONObject(i)
                    FeatureEvidence(
                        feature = Feature.at(o.getInt("f")),
                        sigma = o.getDouble("sigma"),
                        observed = o.getDouble("observed"),
                        usual = o.getDouble("usual"),
                    )
                }
            }.getOrDefault(emptyList())
        }
    }
}
