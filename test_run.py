from dotenv import load_dotenv
import os

load_dotenv()

from graph.state import StoryboardState
from graph.nodes import script_parser_node, shot_planner_node, broll_search_node, pacing_review_node

def test_pipeline():
    with open("sample_scripts/sample1.txt", "r") as f:
        script_text = f.read()
        
    print("Initializing State...")
    state = StoryboardState(raw_script=script_text)
    
    state_dict = script_parser_node(state)
    state = state.model_copy(update={"beats": state_dict["beats"]})
    
    state_dict = shot_planner_node(state)
    state = state.model_copy(update={"beats": state_dict["beats"]})
    
    state_dict = broll_search_node(state)
    state = state.model_copy(update={"beats": state_dict["beats"]})
    
    print("Running PacingReviewAgent (Node 4)...")
    result = pacing_review_node(state)
    
    print("\n--- PACING REVIEW RESULTS ---\n")
    for beat in result["beats"]:
        status = "❌ FLAGGED" if beat.pacing_flag else "✅ PASSED"
        print(f"Beat {beat.beat_id} | {beat.estimated_duration_seconds}s | {beat.shot_type.upper()} | {status}")
        if beat.pacing_flag:
            print(f"  Reason: {beat.pacing_feedback}")
        print("-" * 40)

if __name__ == "__main__":
    test_pipeline()