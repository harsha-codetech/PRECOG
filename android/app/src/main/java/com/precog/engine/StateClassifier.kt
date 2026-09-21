package com.precog.engine

import com.precog.features.Feature
import com.precog.features.FeatureEvidence

/** Maps a deviation score to an ordered state, with the engagement carve-out applied. */
object StateClassifier {

    /** Below this, a baseline is not trustworthy enough to label anything. */
    const val MIN_CONFIDENCE = 0.35

    private const val DISTRACTED_AT = 1.5
    private const val COMPULSIVE_AT = 2.5
    private const val HIGH_RISK_AT = 3.5

    /**
     * Pausing markedly more than usual is the signature of deliberate reading rather than
     * passive consumption. When an otherwise-alerting session carries that signature, it is
     * reported as ENGAGED and no alert is raised. This is the false-positive defence: a
     * person deep in something they chose should not be told they have a problem.
     */
    private const val DELIBERATE_PAUSE_SIGMA = -0.5

    fun classify(
        score: Double,
        confidence: Double,
        evidence: List<FeatureEvidence>,
    ): BehaviouralState {
        if (confidence < MIN_CONFIDENCE) return BehaviouralState.NOT_ENOUGH_PATTERN

        val raw = when {
            score >= HIGH_RISK_AT -> BehaviouralState.HIGH_RISK
            score >= COMPULSIVE_AT -> BehaviouralState.COMPULSIVE
            score >= DISTRACTED_AT -> BehaviouralState.DISTRACTED
            else -> BehaviouralState.NORMAL
        }
        if (!raw.isAlerting) return raw

        val passive = evidence.firstOrNull { it.feature == Feature.UNBROKEN_RATIO }?.sigma ?: 0.0
        val reversals = evidence.firstOrNull { it.feature == Feature.REVERSAL_RATE }?.sigma ?: 0.0
        return if (passive <= DELIBERATE_PAUSE_SIGMA && reversals >= 0.0) BehaviouralState.ENGAGED else raw
    }
}
