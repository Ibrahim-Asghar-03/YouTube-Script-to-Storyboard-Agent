PARSER_PROMPT = """You are a video editor's assistant. Split the following script into
production "beats" — each beat is one continuous visual idea that would be shot as a
single unit (not necessarily one sentence; group 2-3 short related sentences together
if they represent one idea, but split long paragraphs covering multiple ideas).

Rules:
- Preserve every word of the original script, in order.
- Do not summarize, paraphrase, or drop content.
- A typical beat is 1-3 sentences.

Script:
{script}
"""

PLANNER_PROMPT = """You are a video director assigning shot types to a list of script beats.

For each beat, choose exactly one shot_type from:
talking_head, b_roll, text_overlay, screen_recording, graphic_chart

Rules:
- Avoid assigning the same shot_type to more than 2 consecutive beats — vary visuals to
  keep the edit engaging.
- If shot_type is "b_roll", provide 2-3 concrete, literal search terms suitable for a
  stock footage search engine (e.g. "person typing on laptop office", not abstract
  concepts like "productivity").
- Give a one-sentence shot_notes justification for each choice.
{feedback_block}

Beats:
{beats}
"""