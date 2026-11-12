"""
AI Shorts Factory — Script Generator (Phase 1, v3)
Generates 55-65 word English Shorts scripts via local Ollama (Qwen 7B).
Uses an expansion loop to hit the word-count target.
"""

import re
import sys
import requests
from datetime import datetime
from pathlib import Path
# Force UTF-8 output (Windows cp1252 console safety)
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")



# ---------- CONFIG ----------
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "qwen2.5:7b"

PROJECT_ROOT = Path(__file__).parent
SCRIPTS_DIR = PROJECT_ROOT / "output" / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

# Single source of truth for length
MIN_WORDS = 55
MAX_WORDS = 70
MAX_RETRIES = 8

# ---------- SYSTEM PROMPT ----------
SYSTEM_PROMPT = """You are the scriptwriter for "AI Shorts Factory", a faceless English YouTube Shorts channel.

Your job: turn a ONE-LINE topic into a 55-65 word English Shorts script with a REAL story arc.

STRUCTURE (must follow, in order):
1. HOOK (1 sentence): a shocking question, bold claim, or pattern interrupt.
2. SETUP (1 sentence): quick context — what/where/why.
3. BODY (2-3 sentences): punchy facts or a mini-story. Vivid words.
4. PAYOFF (1 sentence): the "wow" moment or lesson.
5. OUTRO (1 sentence): a question or CTA (e.g. "Would you trust one?").

RULES:
- Output ONLY this exact format, nothing else:
TITLE: <max 8 words>
HOOK: <first 6 words of the script>
SCRIPT: <55-65 words, follows the 5-beat structure above>
- Language: English only.
- Tone: curious, fast, dramatic — built for a 30-45 second Short.
- Audience: global viewers aged 16-35, curious about tech and science.
- Every sentence under 14 words. Short, punchy, spoken out loud.
- COUNT THE WORDS in SCRIPT before answering. SCRIPT MUST be 55-65 words.
- If your SCRIPT is under 55 words, ADD another fact sentence. Do not stop early.
- If the topic is unclear, invent a compelling angle and proceed."""


# ---------- HELPERS ----------
def call_ollama(prompt: str, num_predict: int = 600) -> str:
    payload = {
        "model": MODEL,
        "system": SYSTEM_PROMPT,
        "prompt": prompt,
        "stream": False,
        "options": {
            "num_predict": num_predict,
            "temperature": 0.75,
            "top_p": 0.9,
        },
    }
    resp = requests.post(OLLAMA_URL, json=payload, timeout=180)
    resp.raise_for_status()
    return resp.json().get("response", "").strip()


def parse_output(text: str) -> dict:
    fields = {"title": "", "hook": "", "script": ""}
    for line in text.splitlines():
        line = line.strip()
        upper = line.upper()
        if upper.startswith("TITLE:"):
            fields["title"] = line.split(":", 1)[1].strip()
        elif upper.startswith("HOOK:"):
            fields["hook"] = line.split(":", 1)[1].strip()
        elif upper.startswith("SCRIPT:"):
            fields["script"] = line.split(":", 1)[1].strip()
    if not fields["script"]:
        candidates = [l.strip() for l in text.splitlines() if len(l.strip()) > 30]
        if candidates:
            fields["script"] = max(candidates, key=len)
    return fields


def word_count(text: str) -> int:
    return len(re.findall(r"\b[\w'-]+\b", text))


def slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")[:40] or "untitled"


def save_script(topic: str, data: dict) -> Path:
    ts = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    path = SCRIPTS_DIR / f"{ts}_{slugify(topic)}.txt"
    path.write_text(
        f"TOPIC: {topic}\n"
        f"TITLE: {data['title']}\n"
        f"HOOK: {data['hook']}\n"
        f"WORDS: {word_count(data['script'])}\n\n"
        f"SCRIPT:\n{data['script']}\n",
        encoding="utf-8",
    )
    return path


def expand_script(topic: str, current_script: str, current_words: int) -> str:
    """Ask the model to expand an already-written short script."""
    need = MIN_WORDS - current_words
    prompt = (
        f"Topic: {topic}\n\n"
        f"Current SCRIPT ({current_words} words):\n\"{current_script}\"\n\n"
        f"This script is TOO SHORT by {max(need, 1)} words. Expand it to 55-65 words.\n"
        f"- Keep the same topic and tone.\n"
        f"- Add at least {max(need, 10)} more words as new factual sentences.\n"
        f"- Do NOT remove existing sentences. Append and refine.\n"
        f"- Still use short punchy sentences (under 14 words each).\n"
        f"- Keep the TITLE and HOOK lines if they still fit.\n\n"
        f"Output in the exact same format:\n"
        f"TITLE: <max 8 words>\n"
        f"HOOK: <first 6 words of the new script>\n"
        f"SCRIPT: <55-65 words>"
    )
    return call_ollama(prompt)


# ---------- MAIN ----------
def generate_script(topic: str) -> dict:
    user_prompt = (
        f"Topic: {topic}\n\n"
        f"Write the Shorts script now. SCRIPT must be 55-65 words. "
        f"Use the exact output format."
    )

    raw = call_ollama(user_prompt)
    data = parse_output(raw)
    wc = word_count(data["script"])
    print(f"  Pass 1: {wc} words")

    attempt = 2
    while wc < MIN_WORDS and attempt <= MAX_RETRIES:
        print(f"  Expanding (pass {attempt}) ...", end=" ", flush=True)
        raw = expand_script(topic, data["script"], wc)
        data = parse_output(raw)
        wc = word_count(data["script"])
        print(f"{wc} words")
        attempt += 1

    if wc > MAX_WORDS:
        words = data["script"].split()
        data["script"] = " ".join(words[:MAX_WORDS]).rstrip(",;:") + "."
        wc = word_count(data["script"])
        print(f"  Trimmed to {wc} words")

    return data


def main():
    if len(sys.argv) < 2:
        print('Usage: python main.py "Your topic here"')
        sys.exit(1)

    topic = " ".join(sys.argv[1:]).strip()
    print(f"\n🎬 Topic: {topic}\n")

    data = generate_script(topic)
    path = save_script(topic, data)

    print("\n" + "=" * 60)
    print(f"TITLE:  {data['title']}")
    print(f"HOOK:   {data['hook']}")
    print(f"WORDS:  {word_count(data['script'])}")
    print("-" * 60)
    print(data["script"])
    print("=" * 60)
    print(f"\n💾 Saved: {path}\n")


if __name__ == "__main__":
    main()