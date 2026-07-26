from dotenv import load_dotenv
import os

# 1. LOAD THE KEYS FIRST
load_dotenv()

# 2. IMPORT MODULES SECOND
from graph.state import StoryboardState
from graph.nodes import script_parser_node, shot_planner_node, broll_search_node

def test_pipeline():
    with open("sample_scripts/sample1.txt", "r") as f:
        script_text = f.read()
        
    print("Initializing State...")
    state = StoryboardState(raw_script=script_text)
    
    print("Running ScriptParserAgent (Node 1)...")
    state_dict = script_parser_node(state)
    state = state.model_copy(update={"beats": state_dict["beats"]})
    
    print("Running ShotPlannerAgent (Node 2)...")
    state_dict = shot_planner_node(state)
    state = state.model_copy(update={"beats": state_dict["beats"]})
    
    print("Running BRollSearchAgent (Node 3)...")
    result = broll_search_node(state)
    
    print("\n--- FINAL STORYBOARD PLAN WITH MEDIA ---\n")
    for beat in result["beats"]:
        if beat.shot_type == "b_roll":
            print(f"Beat {beat.beat_id} | B-ROLL FOUND:")
            if not beat.broll_assets:
                print("  No assets retrieved (check API keys or terms).")
            for asset in beat.broll_assets:
                print(f"  - Source: {asset.source}")
                print(f"  - Thumbnail: {asset.thumbnail_url}")
                print(f"  - Video: {asset.video_url}")
            print("-" * 40)

if __name__ == "__main__":
    test_pipeline()