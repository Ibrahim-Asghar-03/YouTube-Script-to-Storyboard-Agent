from pydantic import BaseModel, Field, ConfigDict
from enum import Enum
from typing import Optional

class ShotType(str, Enum):
    TALKING_HEAD = "talking_head"
    B_ROLL = "b_roll"
    TEXT_OVERLAY = "text_overlay"
    SCREEN_RECORDING = "screen_recording"
    GRAPHIC_CHART = "graphic_chart"

class BRollAsset(BaseModel):
    source: str                 
    video_url: str
    thumbnail_url: str
    duration_seconds: float
    resolution: str

class Beat(BaseModel):
    model_config = ConfigDict(frozen=True)
    beat_id: int
    text: str
    estimated_word_count: int
    estimated_duration_seconds: float
    shot_type: Optional[ShotType] = None
    shot_notes: Optional[str] = None
    broll_search_terms: list[str] = Field(default_factory=list)
    broll_assets: list[BRollAsset] = Field(default_factory=list)
    pacing_flag: bool = False
    pacing_feedback: Optional[str] = None

class StoryboardState(BaseModel):
    model_config = ConfigDict(frozen=True)
    raw_script: str
    target_wpm: int = 150
    beats: list[Beat] = Field(default_factory=list)
    loop_count: int = 0
    max_loops: int = 1
    errors: list[str] = Field(default_factory=list)