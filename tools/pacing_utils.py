import textstat
from graph.state import Beat, ShotType

MIN_BEAT_SECONDS = 2.5                # below this, a shot can't register visually
MAX_TALKING_HEAD_SECONDS = 14.0        # viewer fatigue threshold, static shot
HIGH_COMPLEXITY_GRADE = 10.0           # Flesch-Kincaid grade level
MAX_COMPLEXITY_DURATION = 6.0          # seconds — too little time to absorb dense info

# Shot types where a viewer genuinely needs time to visually register the
# shot. Punchy one-line talking-head beats and quick text overlays are a
# deliberate, common editing technique — don't flag those as "too short".
DURATION_SENSITIVE_SHOTS = {ShotType.B_ROLL, ShotType.GRAPHIC_CHART}

def evaluate_beat_pacing(beat: Beat) -> tuple[bool, str | None]:
    reasons = []

    if (
        beat.shot_type in DURATION_SENSITIVE_SHOTS
        and beat.estimated_duration_seconds < MIN_BEAT_SECONDS
    ):
        reasons.append(
            f"Beat is only {beat.estimated_duration_seconds}s — too short for this shot to visually register."
        )

    if (
        beat.shot_type == ShotType.TALKING_HEAD
        and beat.estimated_duration_seconds > MAX_TALKING_HEAD_SECONDS
    ):
        reasons.append(
            f"Talking-head beat runs {beat.estimated_duration_seconds}s with no visual break — fatigue risk."
        )

    grade = textstat.flesch_kincaid_grade(beat.text) if beat.text.strip() else 0
    if grade >= HIGH_COMPLEXITY_GRADE and beat.estimated_duration_seconds < MAX_COMPLEXITY_DURATION:
        reasons.append(
            f"Dense content (grade {grade:.1f}) packed into only {beat.estimated_duration_seconds}s."
        )

    flagged = bool(reasons)
    return flagged, (" ".join(reasons) if flagged else None)