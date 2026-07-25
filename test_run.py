from dotenv import load_dotenv
import os

# 1. LOAD THE KEYS FIRST
load_dotenv()

# 2. IMPORT MODULES SECOND
from graph.state import StoryboardState
from graph.nodes import script_parser_node

with open("sample_scripts/sample1.txt", "r") as f:
    script_text = f.read()
    
state = StoryboardState(raw_script=script_text)
result = script_parser_node(state)

for beat in result["beats"]:
    print(f"Beat {beat.beat_id} | {beat.estimated_duration_seconds}s | {beat.text}")