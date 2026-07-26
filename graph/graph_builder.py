from langgraph.graph import StateGraph, END
from graph.state import StoryboardState
from graph.nodes import (
    script_parser_node, 
    shot_planner_node, 
    broll_search_node, 
    pacing_review_node
)

def route_after_pacing(state: StoryboardState) -> str:
    needs_revision = any(b.pacing_flag for b in state.beats)
    
    # loop_count is incremented INSIDE pacing_review_node, before this
    # runs — so by the time we get here it already reflects "passes
    # completed." Must be <= or the very first revision never fires.
    if needs_revision and state.loop_count <= state.max_loops:
        return "revise"
    
    return "done"

def build_graph():
    graph = StateGraph(StoryboardState)
    
    # 1. Define the nodes
    graph.add_node("script_parser", script_parser_node)
    graph.add_node("shot_planner", shot_planner_node)
    graph.add_node("broll_search", broll_search_node)
    graph.add_node("pacing_review", pacing_review_node)
    
    # 2. Set the starting point
    graph.set_entry_point("script_parser")
    
    # 3. Connect the linear path
    graph.add_edge("script_parser", "shot_planner")
    graph.add_edge("shot_planner", "broll_search")
    graph.add_edge("broll_search", "pacing_review")
    
    # 4. Add the conditional loop-back
    graph.add_conditional_edges(
        "pacing_review",
        route_after_pacing,
        {
            "revise": "shot_planner", 
            "done": END
        },
    )
    
    return graph.compile()