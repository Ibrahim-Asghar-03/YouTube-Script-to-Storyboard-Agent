import os
import re
from pydantic import BaseModel, Field, field_validator
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from graph.state import StoryboardState, Beat, ShotType
from graph.prompts import PARSER_PROMPT, PLANNER_PROMPT
from tools.broll_search import search_broll
from graph.state import BRollAsset
from tools.pacing_utils import evaluate_beat_pacing

def get_llm():
    provider = os.environ.get("LLM_PROVIDER", "anthropic").lower()
    
    if provider == "gemini":
        return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0)
    
    # Default to Anthropic for public users
    return ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)

# The pipeline will dynamically use whatever is set in .env
llm = get_llm()

def compute_duration(word_count: int, wpm: int) -> float:
    return round((word_count / wpm) * 60, 2)

# ---- Node 1: ScriptParserAgent -----------------------------------------
class ParsedBeats(BaseModel):
    beats: list[str]

def script_parser_node(state: StoryboardState) -> dict:
    structured_llm = llm.with_structured_output(ParsedBeats)
    result = structured_llm.invoke(PARSER_PROMPT.format(script=state.raw_script))

    raw_beats = result.beats
    # Safety net: LLM returned something degenerate -> fall back to sentence split
    if len(raw_beats) < 2 and len(state.raw_script.split()) > 80:
        sentences = re.split(r"(?<=[.!?])\s+", state.raw_script.strip())
        raw_beats = [" ".join(sentences[i:i + 2]) for i in range(0, len(sentences), 2)]

    beats = []
    for i, text in enumerate(raw_beats):
        wc = len(text.split())
        beats.append(Beat(
            beat_id=i,
            text=text.strip(),
            estimated_word_count=wc,
            estimated_duration_seconds=compute_duration(wc, state.target_wpm),
        ))
    return {"beats": beats}

from pydantic import Field, field_validator

# ---- Node 2: ShotPlannerAgent (+ merged B-roll term generation) --------
class ShotAssignment(BaseModel):
    beat_id: int
    shot_type: ShotType
    shot_notes: str
    broll_search_terms: list[str] = Field(default_factory=list)

    # LLMs drift on formatting ("B-Roll", "Talking Head"). Normalize it before
    # Pydantic tries to coerce the string into the enum, instead of letting
    # a formatting mismatch raise ValidationError and crash the whole run.
    @field_validator("shot_type", mode="before")
    @classmethod
    def _normalize_shot_type(cls, v):
        if isinstance(v, str):
            return v.strip().lower().replace("-", "_").replace(" ", "_")
        return v

class ShotPlan(BaseModel):
    assignments: list[ShotAssignment]

BATCH_SIZE = 20  # beats per planner call keeps structured-output prompt small

def shot_planner_node(state: StoryboardState) -> dict:
    # Revision pass: only re-plan beats that were actually flagged. Leave
    # everything already-fine untouched — saves tokens and avoids the LLM
    # regressing a beat that didn't need changing.
    flagged_beats = [b for b in state.beats if b.pacing_flag]
    
    if state.loop_count > 0 and not flagged_beats:
        return {"beats": state.beats}
        
    beats_to_plan = flagged_beats if state.loop_count > 0 else state.beats
    
    feedback_block = ""
    if flagged_beats:
        lines = "\n".join(f"- Beat {b.beat_id}: {b.pacing_feedback}" for b in flagged_beats)
        feedback_block = f"\nThe previous pass had these pacing issues to fix:\n{lines}\n"

    structured_llm = llm.with_structured_output(ShotPlan)
    all_assignments = []
    
    for i in range(0, len(beats_to_plan), BATCH_SIZE):
        batch = beats_to_plan[i:i + BATCH_SIZE]
        beats_text = "\n".join(f"[{b.beat_id}] {b.text}" for b in batch)
        
        result = structured_llm.invoke(
            PLANNER_PROMPT.format(feedback_block=feedback_block, beats=beats_text)
        )
        all_assignments.extend(result.assignments)

    assignments_by_id = {a.beat_id: a for a in all_assignments}
    
    updated_beats = []
    for b in state.beats:
        if b.beat_id in assignments_by_id:
            a = assignments_by_id[b.beat_id]
            b = b.model_copy(update={
                "shot_type": a.shot_type,
                "shot_notes": a.shot_notes,
                "broll_search_terms": a.broll_search_terms,
                "pacing_flag": False,       # reset — being re-evaluated this pass
                "pacing_feedback": None,
            })
        updated_beats.append(b)
        
    return {"beats": updated_beats}

# ---- Node 3: BRollSearchAgent (pure tool call, no LLM) ------------------
def broll_search_node(state: StoryboardState) -> dict:
    updated_beats = []
    for b in state.beats:
        # Idempotent: skip beats that already have assets and weren't re-flagged
        # don't burn API quota re-querying unchanged beats.
        if b.shot_type == ShotType.B_ROLL and b.broll_search_terms:
            if not b.broll_assets:  
                assets: list[BRollAsset] = []
                for term in b.broll_search_terms[:2]:  # cap calls per beat
                    for r in search_broll(term)[:1]:   # top hit per term
                        assets.append(BRollAsset(**r)) # validate into typed model
                
                b = b.model_copy(update={"broll_assets": assets})
        updated_beats.append(b)
        
    return {"beats": updated_beats}

# ---- Node 4: PacingReviewAgent (rule-based, no LLM) ----------------------
def pacing_review_node(state: StoryboardState) -> dict:
    updated_beats = []
    for b in state.beats:
        flagged, feedback = evaluate_beat_pacing(b)
        updated_beats.append(b.model_copy(update={
            "pacing_flag": flagged,
            "pacing_feedback": feedback,
        }))
    return {"beats": updated_beats, "loop_count": state.loop_count + 1}