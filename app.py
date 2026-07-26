import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

# 1. LOAD ENVIRONMENT VARIABLES FIRST
load_dotenv()

# 2. IMPORT GRAPH MODULES SECOND
from graph.graph_builder import build_graph
from graph.state import StoryboardState

st.set_page_config(page_title="Script-to-Storyboard Agent", layout="wide")
st.title("Script-to-Storyboard Agent")

# Public-demo safety (required, not optional): cap runs per session
MAX_RUNS_PER_SESSION = 5
if "run_count" not in st.session_state:
    st.session_state["run_count"] = 0

raw_script = st.text_area("Paste your script", height=250)
target_wpm = st.sidebar.slider("Narration pace (WPM)", 120, 180, 150)
st.sidebar.caption(f"{MAX_RUNS_PER_SESSION - st.session_state['run_count']} demo run(s) left this session")

if st.button("Generate Storyboard", disabled=st.session_state["run_count"] >= MAX_RUNS_PER_SESSION):
    if not raw_script.strip():
        st.error("Please enter a script first.")
    else:
        st.session_state["run_count"] += 1
        graph = build_graph()
        
        with st.status("Running pipeline...", expanded=True) as status:
            st.write("Parsing script into beats...")
            
            # graph.invoke() returns a plain dict even when the state schema is a Pydantic model.
            raw_result = graph.invoke({"raw_script": raw_script, "target_wpm": target_wpm})
            
            # Always immediately re-wrap it with model_validate to ensure strict typing in the UI
            final_state = StoryboardState.model_validate(raw_result)
            status.update(label="Done", state="complete")
            
        st.success(f"Pipeline completed with {final_state.loop_count - 1} revision loop(s)!")
        
        table_data = []
        
        # Build UI layout
        for b in final_state.beats:
            with st.container(border=True):
                cols = st.columns([1, 4, 3])
                
                with cols[0]:
                    st.markdown(f"**Beat {b.beat_id}**<br>{b.estimated_duration_seconds}s", unsafe_allow_html=True)
                
                with cols[1]:
                    st.write(b.text)
                    st.caption(f"**Shot:** {b.shot_type.upper() if b.shot_type else 'NONE'}")
                
                with cols[2]:
                    if b.broll_assets:
                        st.image(b.broll_assets[0].thumbnail_url, use_container_width=True)
                    st.write(f"**Notes:** {b.shot_notes}")
            
            # Collect data for CSV export
            table_data.append({
                "Beat": b.beat_id,
                "Text": b.text,
                "Duration (s)": b.estimated_duration_seconds,
                "Shot Type": b.shot_type.value if b.shot_type else None,
                "Notes": b.shot_notes,
                "B-Roll Query": ", ".join(b.broll_search_terms) if b.broll_search_terms else "",
            })
            
        df = pd.DataFrame(table_data)
        st.download_button(
            label="Download CSV",
            data=df.to_csv(index=False).encode("utf-8"),
            file_name="storyboard.csv",
            mime="text/csv"
        )