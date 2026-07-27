import re
from pydantic import BaseModel, Field, field_validator
from graph.state import StoryboardState, Beat, ShotType, BRollAsset
from graph.prompts import PARSER_PROMPT, PLANNER_PROMPT
from graph.llm_factory import get_llm, get_fallback_llm
from tools.broll_search import search_broll_batch
from tools.pacing_utils import evaluate_beat_pacing

def compute_duration(word_count: int, wpm: int) -> float:
    return round((word_count / wpm) * 60, 2)

def invoke_structured(prompt_text: str, schema, node_name: str):
    try:
        # 1. Try Primary (Gemini)
        return get_llm(node_name).with_structured_output(schema).invoke(prompt_text)
    except Exception as primary_error:
        print(f"⚠️ Primary LLM failed: {primary_error}. Trying fallback...")
        
        try:
            # 2. Try Fallback (Anthropic)
            return get_fallback_llm(node_name).with_structured_output(schema).invoke(prompt_text)
        except Exception as fallback_error:
            # 3. If BOTH fail, raise a combined error so we can actually see Gemini's error!
            raise RuntimeError(
                f"\n[PRIMARY GEMINI ERROR]: {primary_error}\n\n"
                f"[FALLBACK ANTHROPIC ERROR]: {fallback_error}"
            )

# ---- Node 1: ScriptParserAgent -----------------------------------------
class ParsedBeats(BaseModel):
    beats: list[str]

def script_parser_node(state: StoryboardState) -> dict:
    try:
        result = invoke_structured(PARSER_PROMPT.format(script=state.raw_script), ParsedBeats, "script_parser")
        raw_beats = result.beats
    except Exception as e:
        if len(state.raw_script.split()) > 80:
            sentences = re.split(r"(?<=[.!?])\s+", state.raw_script.strip())
            raw_beats = [" ".join(sentences[i:i + 2]) for i in range(0, len(sentences), 2)]
        else:
            raise RuntimeError(f"Script parsing failed: {e}")

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

# ---- Node 2: ShotPlannerAgent -------------------------------------------
class ShotAssignment(BaseModel):
    beat_id: int
    shot_type: ShotType
    shot_notes: str
    broll_search_terms: list[str] = Field(default_factory=list)

    @field_validator("shot_type", mode="before")
    @classmethod
    def _normalize_shot_type(cls, v):
        if isinstance(v, str):
            return v.strip().lower().replace("-", "_").replace(" ", "_")
        return v

class ShotPlan(BaseModel):
    assignments: list[ShotAssignment]

BATCH_SIZE = 20

def _neighbor_context(all_beats: list[Beat], beat_id: int) -> str:
    idx = next((i for i, b in enumerate(all_beats) if b.beat_id == beat_id), None)
    if idx is None:
        return ""
    parts = []
    if idx > 0 and all_beats[idx - 1].shot_type:
        parts.append(f"previous={all_beats[idx - 1].shot_type.value}")
    if idx < len(all_beats) - 1 and all_beats[idx + 1].shot_type:
        parts.append(f"next={all_beats[idx + 1].shot_type.value}")
    return f" [{', '.join(parts)}]" if parts else ""

def shot_planner_node(state: StoryboardState) -> dict:
    is_revision = state.loop_count > 0
    targets = [b for b in state.beats if b.pacing_flag] if is_revision else state.beats
    
    if not targets:
        return {"beats": list(state.beats)}
        
    assignments_by_id: dict[int, ShotAssignment] = {}
    
    for i in range(0, len(targets), BATCH_SIZE):
        batch = targets[i:i + BATCH_SIZE]
        
        feedback_block = ""
        flagged_in_batch = [b for b in batch if b.pacing_flag]
        if flagged_in_batch:
            lines = "\n".join(f"- Beat {b.beat_id}: {b.pacing_feedback}" for b in flagged_in_batch)
            feedback_block = f"\nThe previous pass had these pacing issues to fix:\n{lines}\n"

        beats_text = "\n".join(
            f"[{b.beat_id}] {b.text}{_neighbor_context(state.beats, b.beat_id)}" 
            for b in batch
        )
        
        try:
            prompt = PLANNER_PROMPT.format(feedback_block=feedback_block, beats=beats_text)
            result = invoke_structured(prompt, ShotPlan, "shot_planner")
            assignments_by_id.update({a.beat_id: a for a in result.assignments})
        except Exception as e:
            raise RuntimeError(f"Shot Planner failed during LLM invocation: {e}")

    updated_beats = []
    for b in state.beats:
        a = assignments_by_id.get(b.beat_id)
        if a:
            b = b.model_copy(update={
                "shot_type": a.shot_type,
                "shot_notes": a.shot_notes,
                "broll_search_terms": a.broll_search_terms,
                "pacing_flag": False,
                "pacing_feedback": None,
            })
        updated_beats.append(b)
        
    return {"beats": updated_beats}

# ---- Node 3: BRollSearchAgent -------------------------------------------
def broll_search_node(state: StoryboardState) -> dict:
    pending = [
        b for b in state.beats 
        if b.shot_type == ShotType.B_ROLL and b.broll_search_terms and not b.broll_assets
    ]
    
    if not pending:
        return {"beats": list(state.beats)}
        
    pending_ids = {b.beat_id for b in pending}
    all_queries = [term for b in pending for term in b.broll_search_terms[:2]]
    results_by_query = search_broll_batch(all_queries)
    
    updated_beats = []
    for b in state.beats:
        if b.beat_id in pending_ids:
            assets = [
                BRollAsset(**results_by_query[term][0])
                for term in b.broll_search_terms[:2]
                if results_by_query.get(term)
            ]
            b = b.model_copy(update={"broll_assets": assets})
        updated_beats.append(b)
        
    return {"beats": updated_beats}

# ---- Node 4: PacingReviewAgent ------------------------------------------
def pacing_review_node(state: StoryboardState) -> dict:
    updated_beats = []
    for b in state.beats:
        flagged, feedback = evaluate_beat_pacing(b)
        updated_beats.append(b.model_copy(update={
            "pacing_flag": flagged,
            "pacing_feedback": feedback,
        }))
    return {"beats": updated_beats, "loop_count": state.loop_count + 1}