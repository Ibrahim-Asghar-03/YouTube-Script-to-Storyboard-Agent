CSS_BLOCK = """
<style>
:root {
  --bg-primary: #18181b; 
  --bg-panel: #202023; 
  --bg-card: #27272a;
  --border-color: #3f3f46; 
  --text-primary: #e4e4e7; 
  --text-secondary: #a1a1aa;
  --accent: #3b82f6; 
  --warning: #f59e0b;
  --font-ui: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

.stApp { background-color: var(--bg-primary); font-family: var(--font-ui); color: var(--text-primary); }
[data-testid="stSidebar"] { background-color: var(--bg-panel); border-right: 1px solid var(--border-color); }
.block-container { padding-top: 1.5rem; max-width: 100%; }

.stButton > button {
  background-color: var(--bg-card); color: var(--text-primary);
  border: 1px solid var(--border-color); border-radius: 4px;
  padding: 0.4rem 1rem; font-size: 0.85rem; font-weight: 500;
  transition: all 0.2s ease;
}
.stButton > button:hover { border-color: var(--accent); color: var(--accent); }

.beat-card {
  background-color: var(--bg-card); border: 1px solid var(--border-color);
  border-radius: 6px; padding: 0.8rem 1rem; margin-bottom: 0.6rem;
}
.beat-card.flagged { border-left: 4px solid var(--warning); }

.shot-badge {
  display: inline-block; font-size: 0.7rem; font-weight: 600;
  letter-spacing: 0.04em; text-transform: uppercase;
  padding: 0.15rem 0.5rem; border: 1px solid var(--border-color);
  border-radius: 4px; color: var(--text-secondary); background: var(--bg-panel);
}

.timeline-track {
  display: flex; width: 100%; height: 32px;
  border: 1px solid var(--border-color); border-radius: 4px; overflow: hidden;
  background-color: var(--bg-panel); margin-bottom: 1rem;
}
.timeline-segment {
  height: 100%; border-right: 1px solid var(--bg-primary);
  display: flex; align-items: center; justify-content: center;
  font-size: 0.7rem; font-weight: 500; color: var(--text-primary);
}
</style>
"""