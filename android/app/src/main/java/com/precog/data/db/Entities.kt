package com.precog.data.db

import androidx.room.ColumnInfo
import androidx.room.Entity
import androidx.room.Index
import androidx.room.PrimaryKey

/**
 * Raw accessibility scroll event. Timing and scroll magnitude only — never content.
 * Rows are purged after RAW_RETENTION_MS (see PrecogRepository); they exist so a
 * changed feature extractor can be re-run over recent data, not as an archive.
 */
@Entity(tableName = "scroll_events", indices = [Index("tsMs"), Index("pkg")])
data class ScrollEventEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val tsMs: Long,
    val pkg: String,
    /** Resolved scroll magnitude in pixels, or null when the app exposes neither signal. */
    val delta: Int?,
    /** true when [delta] came from scrollY differencing rather than scrollDeltaY. */
    val deltaFromScrollY: Boolean,
)

/**
 * One feature window — the unit the baseline is built over and the unit that is scored.
 * WINDOW_SIZE consecutive scroll events inside a single session.
 */
@Entity(tableName = "feature_windows", indices = [Index("sessionId"), Index("cellKey"), Index("tsMs")])
data class FeatureWindowEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val sessionId: Long,
    val tsMs: Long,
    val pkg: String,
    val bucket: Int,
    val cellKey: String,
    val logMedianGap: Double,
    val burstiness: Double,
    /**
     * Fraction of inter-event gaps below UNBROKEN_GAP_MS. Deliberately NOT the SPEC's
     * `passive_ratio` (windows with scrolls and zero clicks), which is a different
     * quantity. The column name is pinned to the original spelling so existing
     * on-device baselines survive the rename.
     */
    @ColumnInfo(name = "passiveRatio") val unbrokenRatio: Double,
    val reversalRate: Double,
    val logDeltaMag: Double,
    val eventRate: Double,
    /** Deviation score in robust-sigma units; null until a baseline for this cell exists. */
    val score: Double?,
    /** Ordinal of BehaviouralState, or null while unscored. */
    val stateOrdinal: Int?,
)

@Entity(tableName = "sessions", indices = [Index("startMs"), Index("pkg")])
data class SessionEntity(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val pkg: String,
    val startMs: Long,
    val endMs: Long,
    val eventCount: Int,
    val windowCount: Int,
    val bucket: Int,
    val peakScore: Double?,
    val medianScore: Double?,
    val stateOrdinal: Int?,
    val confidence: Double,
    /** JSON array of [FeatureEvidence] — the per-feature evidence for this session's state. */
    val evidenceJson: String?,
    /** User feedback on the state call: null = none, 0 = "that's not me", 1 = "that was me". */
    val feedback: Int?,
)

/** A fitted baseline for one context cell (app x time-of-day). Model params live in JSON. */
@Entity(tableName = "baseline_cells")
data class BaselineCellEntity(
    @PrimaryKey val cellKey: String,
    val pkg: String,
    val bucket: Int,
    val n: Int,
    val updatedMs: Long,
    val modelJson: String,
)
