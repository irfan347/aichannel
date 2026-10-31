"""Step 1: topic -> structured script (scenes) using the Claude API."""
import json, os, re
import anthropic

PROMPT = """You write scripts for a faceless YouTube channel about AI. Topic: {topic}

Return ONLY JSON:
{{
  "title": "clickable title under 70 chars",
  "description": "2-3 sentence description with a call to subscribe",
  "tags": ["8-12 tags"],
  "scenes": [
    {{"narration": "1-3 spoken sentences", "visual": "2-3 word stock footage search phrase"}}
  ]
}}
Rules: {n} scenes, ~{secs} seconds total spoken. Scene 1 is a strong hook. Last scene is a
short call to action. Plain conversational English, no emojis, no stage directions.
Only state facts you are confident about."""


def generate_script(topic: str, scenes: int = 8, seconds: int = 60) -> dict:
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model=os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5"),
        max_tokens=2000,
        messages=[{"role": "user", "content": PROMPT.format(topic=topic, n=scenes, secs=seconds)}],
    )
    text = msg.content[0].text
    m = re.search(r"\{.*\}", text, re.S)
    return json.loads(m.group(0))
