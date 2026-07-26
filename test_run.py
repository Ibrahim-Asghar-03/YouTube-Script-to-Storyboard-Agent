from dotenv import load_dotenv
import os

# 1. LOAD THE KEYS FIRST
load_dotenv()

# 2. IMPORT MODULES SECOND
from graph.state import StoryboardState
from graph.nodes import script_parser_node, shot_planner_node

def test_pipeline():
    with open("sample_scripts/sample1.txt", "r") as f:
        script_text = f.read()
        
    print("Initializing State...")
    state = StoryboardState(raw_script=script_text)
    
    print("Running ScriptParserAgent (Node 1)...")
    state_dict = script_parser_node(state)
    
    # Update state with parsed beats
    state = state.model_copy(update={"beats": state_dict["beats"]})
    
    print("Running ShotPlannerAgent (Node 2)...")
    result = shot_planner_node(state)
    
    print("\n--- FINAL STORYBOARD PLAN ---\n")
    for beat in result["beats"]:
        print(f"Beat {beat.beat_id} | {beat.estimated_duration_seconds}s")
        print(f"Text: {beat.text}")
        print(f"Shot Type: {beat.shot_type.upper() if beat.shot_type else 'NONE'}")
        print(f"Notes: {beat.shot_notes}")
        if beat.broll_search_terms:
            print(f"Search Terms: {', '.join(beat.broll_search_terms)}")
        print("-" * 40)

if __name__ == "__main__":
    test_pipeline()