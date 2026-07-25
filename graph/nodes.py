from langchain_anthropic import ChatAnthropic
from pydantic import BaseModel, Field, field_validator
from graph.state import StoryboardState, Beat, ShotType
from graph.prompts import PARSER_PROMPT, PLANNER_PROMPT
import re

# Cheap, fast model — this task is structured extraction, not deep reasoning
llm = ChatAnthropic(model="claude-haiku-4-5-20251001", temperature=0)

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