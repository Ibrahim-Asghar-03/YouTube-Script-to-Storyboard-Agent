from dotenv import load_dotenv
import os

load_dotenv()

from graph.state import StoryboardState
from graph.graph_builder import build_graph

def test_full_agent():
    with open("sample_scripts/sample1.txt", "r") as f:
        script_text = f.read()
        
    print("Compiling Agent Graph...")
    agent = build_graph()
    
    print("Invoking Pipeline (This might take 15-30 seconds depending on API speed)...\n")
    
    # We pass the raw dict from agent.invoke() back into our Pydantic model for strict validation
    raw_result = agent.invoke({"raw_script": script_text})
    final_state = StoryboardState.model_validate(raw_result)
    
    print("=== FINAL OUTPUT ===")
    print(f"Total Revision Loops Executed: {final_state.loop_count - 1}\n")
    
    for beat in final_state.beats:
        print(f"[{beat.beat_id}] {beat.estimated_duration_seconds}s | {beat.shot_type.upper()}")
        print(f"Text: {beat.text}")
        if beat.shot_type == "b_roll" and beat.broll_assets:
            print(f"B-Roll: {beat.broll_assets[0].video_url}")
        print("-" * 40)

if __name__ == "__main__":
    test_full_agent()