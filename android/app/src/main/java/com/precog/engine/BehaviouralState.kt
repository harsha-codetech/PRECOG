package com.precog.engine

import com.precog.features.FeatureEvidence

/**
 * The ordered behavioural states, plus the two honest non-answers.
 *
 * Language is behavioural throughout. PRECOG describes deviation from a person's own
 * pattern; it does not diagnose anything, and no label here is a clinical claim.
 */
enum class BehaviouralState(
    val title: String,
    val summary: String,
    val isAlerting: Boolean,
) {
    /** Not enough data yet. Shown during enrolment. */
    LEARNING("Still learning", "PRECOG is watching how you normally scroll. No readings yet.", false),

    /**
     * Enrolled, but this person's scrolling is too varied for a usable baseline.
     * Saying so is the point: not every person has a stable behavioural signature, and
     * inventing certainty for those who do not is the failure mode this state exists to avoid.
     */
    NOT_ENOUGH_PATTERN("No clear pattern", "Your scrolling varies too much for PRECOG to call anything unusual. That is a real result, not a fault.", false),

    NORMAL("Normal", "This session looks like how you usually scroll.", false),

    /** Deliberate long use: the false-positive defence, never an alert. */
    ENGAGED("Engaged", "A long session, but you are pacing it — pausing and going back. That reads as deliberate, not lost time.", false),

    DISTRACTED("Distracted", "Your rhythm has drifted from your usual pattern.", true),

    COMPULSIVE("Compulsive", "A sustained, uninterrupted rhythm well outside your usual range.", true),

    HIGH_RISK("High risk", "Strongly outside your usual pattern for this app and time of day.", true);

    companion object {
        fun fromOrdinal(i: Int?) = i?.let { entries.getOrNull(it) }
    }
}

/**
 * The output of scoring one window or session. The score never travels without its
 * evidence — a bare number the user cannot interrogate is the thing this project
 * exists to avoid producing.
 */
data class DeviationResult(
    val score: Double,
    val state: BehaviouralState,
    val confidence: Double,
    val evidence: List<FeatureEvidence>,
    val pcaSigma: Double,
    val gmmSigma: Double,
) {
    val confidenceLabel: String get() = when {
        confidence >= 0.75 -> "High"
        confidence >= 0.50 -> "Moderate"
        confidence >= 0.35 -> "Low"
        else -> "Too low to call"
    }
}
