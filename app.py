import streamlit as st
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()

from graph.graph_builder import build_graph
from graph.state import StoryboardState, Beat
from graph.ui_theme import CSS_BLOCK

st.set_page_config(page_title="Storyboard", layout="wide", initial_sidebar_state="collapsed")
st.markdown(CSS_BLOCK, unsafe_allow_html=True)
st.title("🎬 Script-to-Storyboard Agent")

SHOT_COLORS = {
    "talking_head": "#3f3f46", "b_roll": "#3b82f6", "text_overlay": "#71717a",
    "screen_recording": "#0d9488", "graphic_chart": "#0891b2",
}

def render_timeline(beats: list[Beat]) -> str:
    total = sum(b.estimated_duration_seconds for b in beats) or 1
    segments = "".join(
        f'<div class="timeline-segment" style="width:{max((b.estimated_duration_seconds / total) * 100, 2.0):.2f}%;'
        f'background-color:{SHOT_COLORS.get(b.shot_type.value if b.shot_type else "talking_head", "#3f3f46")};" '
        f'title="Beat {b.beat_id}: {b.estimated_duration_seconds}s">B{b.beat_id}</div>'
        for b in beats
    )
    return f'<div class="timeline-track">{segments}</div>'

@st.dialog("Beat preview")
def show_video_modal(beat: Beat):
    st.markdown(f"**Beat {beat.beat_id}** · {beat.shot_type.value if beat.shot_type else 'NONE'}")
    st.write(beat.text)
    if beat.broll_assets:
        st.video(beat.broll_assets[0].video_url)
        st.caption(f"Source: {beat.broll_assets[0].source.upper()} | Resolution: {beat.broll_assets[0].resolution}")
    else:
        st.info("No b-roll asset for this beat.")

MAX_RUNS_PER_SESSION = 5
st.session_state.setdefault("run_count", 0)

left, right = st.columns([1, 1.6], gap="medium")

with left:
    st.markdown("#### Script Input")
    script = st.text_area("script", height=320, label_visibility="collapsed", placeholder="Paste your script...")
    target_wpm = st.slider("Narration pace (WPM)", 120, 180, 150)
    runs_left = MAX_RUNS_PER_SESSION - st.session_state.run_count
    st.caption(f"{runs_left} demo run(s) left this session")
    generate = st.button("Generate Storyboard", use_container_width=True, disabled=not script.strip() or runs_left <= 0)

if generate:
    st.session_state.run_count += 1
    with st.spinner("Running pipeline..."):
        try:
            raw = build_graph().invoke(StoryboardState(raw_script=script, target_wpm=target_wpm))
            st.session_state.result = StoryboardState.model_validate(raw)
        except Exception as e:
            st.error(f"Pipeline Execution Failed: {str(e)}")

with right:
    if "result" in st.session_state:
        result = st.session_state.result
        st.markdown("#### Timeline Track")
        st.markdown(render_timeline(result.beats), unsafe_allow_html=True)
        st.markdown("#### Storyboard Beats")

        cols = st.columns(3)
        for i, b in enumerate(result.beats):
            with cols[i % 3]:
                flagged = "flagged" if b.pacing_flag else ""
                shot_label = b.shot_type.value if b.shot_type else "NONE"
                st.markdown(f'''
                    <div class="beat-card {flagged}">
                        <span class="shot-badge">{shot_label}</span>
                        <div style="font-size:0.8rem;margin-top:0.35rem;">{b.text[:90]}...</div>
                        <div style="color:var(--text-secondary);font-size:0.7rem;margin-top:0.3rem;">
                            {b.estimated_duration_seconds}s | {b.shot_notes or ""}
                        </div>
                    </div>
                ''', unsafe_allow_html=True)
                
                if b.shot_type == "b_roll" and b.broll_assets:
                    if st.button("▶ Preview B-Roll", key=f"preview_{b.beat_id}", use_container_width=True):
                        show_video_modal(b)

        st.markdown("---")
        df = pd.DataFrame([{
            "Beat": b.beat_id, "Text": b.text, "Duration (s)": b.estimated_duration_seconds,
            "Shot Type": b.shot_type.value if b.shot_type else None, "Notes": b.shot_notes,
        } for b in result.beats])
        st.download_button("📥 Download CSV", df.to_csv(index=False).encode("utf-8"), "storyboard.csv", "text/csv")