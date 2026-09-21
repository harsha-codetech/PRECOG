package com.precog.data.db

import androidx.room.Dao
import androidx.room.Insert
import androidx.room.Query
import androidx.room.Upsert
import kotlinx.coroutines.flow.Flow

@Dao
interface ScrollEventDao {
    @Insert suspend fun insertAll(rows: List<ScrollEventEntity>)

    @Query("DELETE FROM scroll_events WHERE tsMs < :cutoffMs")
    suspend fun purgeBefore(cutoffMs: Long): Int

    @Query("SELECT COUNT(*) FROM scroll_events")
    fun countFlow(): Flow<Int>
}

@Dao
interface FeatureWindowDao {
    @Insert suspend fun insertAll(rows: List<FeatureWindowEntity>): List<Long>

    @Query("SELECT * FROM feature_windows WHERE cellKey = :cellKey ORDER BY tsMs DESC LIMIT :limit")
    suspend fun forCell(cellKey: String, limit: Int): List<FeatureWindowEntity>

    @Query("SELECT * FROM feature_windows ORDER BY tsMs DESC LIMIT :limit")
    suspend fun recent(limit: Int): List<FeatureWindowEntity>

    @Query("SELECT * FROM feature_windows WHERE sessionId = :sessionId ORDER BY tsMs ASC")
    suspend fun forSession(sessionId: Long): List<FeatureWindowEntity>

    @Query("SELECT COUNT(*) FROM feature_windows")
    fun totalFlow(): Flow<Int>

    @Query("SELECT COUNT(*) FROM feature_windows")
    suspend fun total(): Int

    @Query("SELECT cellKey FROM feature_windows GROUP BY cellKey HAVING COUNT(*) >= :minN")
    suspend fun eligibleCells(minN: Int): List<String>

    @Query("UPDATE feature_windows SET score = :score, stateOrdinal = :state WHERE id = :id")
    suspend fun setScore(id: Long, score: Double, state: Int)
}

@Dao
interface SessionDao {
    @Insert suspend fun insert(row: SessionEntity): Long

    @Query("SELECT * FROM sessions ORDER BY startMs DESC LIMIT :limit")
    fun recentFlow(limit: Int): Flow<List<SessionEntity>>

    @Query("SELECT * FROM sessions WHERE startMs >= :sinceMs ORDER BY startMs DESC")
    fun sinceFlow(sinceMs: Long): Flow<List<SessionEntity>>

    @Query("SELECT * FROM sessions WHERE id = :id")
    fun byIdFlow(id: Long): Flow<SessionEntity?>

    @Query("UPDATE sessions SET feedback = :feedback WHERE id = :id")
    suspend fun setFeedback(id: Long, feedback: Int)

    @Query("UPDATE sessions SET peakScore = :peak, medianScore = :median, stateOrdinal = :state, confidence = :conf, evidenceJson = :evidence WHERE id = :id")
    suspend fun setOutcome(id: Long, peak: Double?, median: Double?, state: Int?, conf: Double, evidence: String?)

    @Query("SELECT COUNT(*) FROM sessions")
    fun countFlow(): Flow<Int>
}

@Dao
interface BaselineDao {
    @Upsert suspend fun upsert(row: BaselineCellEntity)

    @Query("SELECT * FROM baseline_cells WHERE cellKey = :cellKey")
    suspend fun byKey(cellKey: String): BaselineCellEntity?

    @Query("SELECT * FROM baseline_cells ORDER BY n DESC")
    suspend fun all(): List<BaselineCellEntity>

    @Query("SELECT * FROM baseline_cells ORDER BY n DESC")
    fun allFlow(): Flow<List<BaselineCellEntity>>

    @Query("DELETE FROM baseline_cells")
    suspend fun clear()
}
