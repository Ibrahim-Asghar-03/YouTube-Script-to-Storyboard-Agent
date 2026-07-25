# YouTube Script-to-Storyboard Agent

An AI-driven pipeline built with **LangGraph** that converts raw YouTube scripts into structured, shot-level storyboards — complete with automated B-roll sourcing and deterministic pacing analysis.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Pipeline Components](#pipeline-components)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
- [Running the Application](#running-the-application)
- [Testing](#testing)
- [Design Decisions](#design-decisions)
- [License](#license)

---

## Overview

Video editors and YouTube automation creators routinely spend hours manually breaking scripts into beat sheets, researching B-roll search terms, and estimating visual pacing before editing can even begin.

This project automates that entire pre-production workflow. By combining LLM-driven structured extraction with deterministic, rule-based algorithms, the YouTube Script-to-Storyboard Agent produces production-ready shot plans, sources real-time stock footage, and self-corrects pacing issues through a stateful loop-back architecture.

---

## Architecture

The pipeline is implemented as a linear state graph with a single controlled loop-back edge. Of the four graph nodes, only two invoke an LLM — B-roll search and pacing review are pure deterministic Python functions, which minimizes latency, cost, and non-determinism where AI reasoning isn't required.

```mermaid
flowchart TD
    START([START]) --> SP[ScriptParserAgent<br/>LLM Structured Output]
    SP --> SHP[ShotPlannerAgent<br/>LLM: Shot Type + Search Terms]
    SHP --> BR[BRollSearchAgent<br/>Tool Call: Pexels / Pixabay API]
    BR --> PR[PacingReviewAgent<br/>Deterministic Rule-Based Engine]
    PR -->|Flags Found & Loop Count < Max| SHP
    PR -->|Clean or Loop Exhausted| DONE([Render Storyboard])
```

---

## Pipeline Components

| Node | Type | Description |
|---|---|---|
| `ScriptParserAgent` | LLM | Splits the raw script into semantic visual "beats" (1–3 sentences per visual idea), with a regex-based sentence-splitting fallback for reliability. |
| `ShotPlannerAgent` | LLM | Assigns shot types (`talking_head`, `b_roll`, `text_overlay`, etc.), production notes, and 2–3 concrete stock search terms per beat. Incorporates feedback on loop-back runs. |
| `BRollSearchAgent` | Tool | Queries the Pexels and Pixabay APIs. Includes query-level LRU caching and exponential backoff for rate-limit handling. |
| `PacingReviewAgent` | Rule Engine | Deterministically evaluates beats for visual fatigue, minimum shot duration, and readability (via Flesch-Kincaid complexity metrics). |

---

## Repository Structure

```text
yt-storyboard-agent/
├── app.py                     # Streamlit frontend application
├── graph/                     # LangGraph state machine and nodes
│   ├── __init__.py
│   ├── state.py                # Pydantic schemas (Beat, StoryboardState, ShotType)
│   ├── prompts.py               # System and agent instruction prompts
│   ├── nodes.py                 # Node implementations (Parser, Planner, Search, Review)
│   └── graph_builder.py         # StateGraph assembly and conditional routing
├── tools/                     # Deterministic utilities and external API clients
│   ├── __init__.py
│   ├── broll_search.py          # Pexels and Pixabay API integrations
│   └── pacing_utils.py          # Rule-based pacing and readability algorithms
├── tests/                     # Unit and integration test suite
│   ├── test_parser.py
│   ├── test_planner.py
│   ├── test_broll.py
│   └── test_pacing.py
├── sample_scripts/            # Sample scripts for validation
├── requirements.txt           # Project dependencies
├── .env.example                # Template for required environment variables
└── README.md
```

---

## Getting Started

### Prerequisites

- Python 3.10+
- Anthropic API key (Claude models)
- Pexels and/or Pixabay API key (free tiers supported)

### Installation

```bash
git clone https://github.com/MuhammadTaha03/YouTube-Script-to-Storyboard-Agent.git
cd YouTube-Script-to-Storyboard-Agent

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Environment Configuration

Copy the example environment file and populate it with your credentials:

```bash
cp .env.example .env
```

```env
ANTHROPIC_API_KEY=your_anthropic_key_here
PEXELS_API_KEY=your_pexels_key_here
PIXABAY_API_KEY=your_pixabay_key_here

# Optional: LangSmith observability
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your_langchain_key_here
LANGCHAIN_PROJECT=yt-storyboard-agent
```

---

## Running the Application

```bash
streamlit run app.py
```

1. Open `http://localhost:8501` in your browser.
2. Paste your YouTube narration script or upload a text file.
3. Adjust the **Narration Pace (WPM)** slider in the sidebar (default: 150 WPM).
4. Click **Generate Storyboard** to view and export the production plan (CSV or Markdown).

---

## Testing

Run the deterministic test suite (no API calls required):

```bash
pytest tests/
```

- **Rule Engine Tests** — Validate pacing flags against edge-case beats (e.g., a static talking-head shot exceeding 14 seconds).
- **Loop-Termination Tests** — Confirm the graph halts execution after exactly one revision loop.
- **API Cache Tests** — Verify `lru_cache` behavior and fallback handling for stock footage queries.

---

## Design Decisions

- **Deterministic word/duration calculation** — Word counts and time estimates are computed in Python rather than by the LLM, avoiding arithmetic inaccuracies.
- **Infinite loop prevention** — The conditional route `state.loop_count < state.max_loops` hard-caps execution to prevent runaway retry loops.
- **Fail-safe parsing** — A regex sentence splitter automatically engages if the LLM response fails or degrades on long scripts.

---

## License

Distributed under the MIT License. See [`LICENSE`](LICENSE) for details.
