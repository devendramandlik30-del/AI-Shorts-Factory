
"""
AI Shorts Factory — Script Generator (Phase 1)
Generates 55-70 word English YouTube Shorts scripts using Gemini API.
Includes automatic expansion, validation, and error handling.
"""

import os
import re
import sys
import requests

from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv


# ---------- WINDOWS CONFIGURATION ----------

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

load_dotenv(override=True)

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip().strip('"').strip("'")

# Model can be changed through .env without editing Python code.
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash").strip()

GEMINI_URL = (
    f"https://generativelanguage.googleapis.com/v1beta/models/"
    f"{GEMINI_MODEL}:generateContent"
)

PROJECT_ROOT = Path(__file__).resolve().parent
SCRIPTS_DIR = PROJECT_ROOT / "output" / "scripts"
SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------- SCRIPT SETTINGS ----------

MIN_WORDS = 55
MAX_WORDS = 70
MAX_RETRIES = 6


# ---------- SYSTEM PROMPT ----------


SYSTEM_PROMPT = """
You are a professional YouTube Shorts scriptwriter.

Write one engaging English YouTube Shorts script.

Requirements:
- Script length: 55 to 65 words.
- Use simple, natural English.
- Start with an interesting hook.
- Include relevant facts.
- Build curiosity and deliver a satisfying payoff.
- End with an engaging question.
- Keep sentences short and conversational.
- Do not repeat information.

Return exactly:

TITLE: <maximum 8 words>
HOOK: <first 6 words of script>
SCRIPT:
<complete 55-65 word script>

Do not include explanations or additional text.
"""


# ---------- API ERROR HANDLING ----------


import time
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    RetryError,
)

# List of models to try in order (primary first, then fallbacks)
GEMINI_MODELS = [
    "gemini-3.8-flash",        
    "gemini-3.6-flash",       
    "gemini-3.5-flash-lite",   
]

class GeminiTransientError(Exception):
    """Custom exception for transient Gemini errors (503, 429, etc.)"""
    pass


def _call_gemini_once(model: str, prompt: str, num_predict: int) -> str:
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    headers = {
        "x-goog-api-key": GEMINI_API_KEY,
        "Content-Type": "application/json",
    }
    body = {
        "contents": [{"parts": [{"text": f"{SYSTEM_PROMPT}\n\n{prompt}"}]}],
        "generationConfig": {
            "maxOutputTokens": num_predict,
            "thinkingConfig": {"thinkingLevel": "low"},
        },
    }
    resp = requests.post(url, headers=headers, json=body, timeout=(30, 300))

    if resp.status_code in (429, 500, 502, 503, 504):
        raise RuntimeError(f"TRANSIENT {resp.status_code}: {resp.text[:200]}")

    resp.raise_for_status()
    data = resp.json()
    candidates = data.get("candidates", [])
    if not candidates:
        raise RuntimeError(f"No candidates returned: {data}")
    return candidates[0]["content"]["parts"][0]["text"].strip()


def call_llm(prompt: str, num_predict: int = 600) -> str:
    last_error = None
    for model in GEMINI_MODELS:
        print(f"   Trying model: {model}")
        for attempt in range(1, 4):
            try:
                return _call_gemini_once(model, prompt, num_predict)
            except RuntimeError as e:
                if "TRANSIENT" in str(e):
                    wait = min(2 ** attempt, 20)
                    print(f"   ⚠ {model} transient error, retry in {wait}s (attempt {attempt}/3)")
                    time.sleep(wait)
                    last_error = e
                    continue
                else:
                    print(f"   ✗ {model} non-transient error: {e}")
                    last_error = e
                    break
            except requests.exceptions.Timeout:
                print(f"   ✗ {model} timed out after 300s")
                last_error = e
                break
    raise RuntimeError(f"All Gemini models failed. Last error: {last_error}")

# ---------- OUTPUT PARSER ----------

def parse_output(text: str) -> dict:
    fields = {"title": "", "hook": "", "script": ""}

    # First try the inline form: "SCRIPT: <text on same line>"
    m = re.search(r"^TITLE:\s*(.+)$", text, re.MULTILINE)
    if m:
        fields["title"] = m.group(1).strip()

    m = re.search(r"^HOOK:\s*(.+)$", text, re.MULTILINE)
    if m:
        fields["hook"] = m.group(1).strip()

    # SCRIPT can be inline OR on following lines until blank line / next label / end
    m = re.search(r"^SCRIPT:\s*(.+?)(?=\n\s*\n|\Z)", text, re.MULTILINE | re.DOTALL)
    if m:
        fields["script"] = " ".join(m.group(1).split()).strip()

    # Fallback: longest paragraph if SCRIPT label missing entirely
    if not fields["script"]:
        paras = [" ".join(p.split()) for p in text.split("\n\n") if len(p.strip()) > 40]
        if paras:
            fields["script"] = max(paras, key=len)

    return fields

# ---------- WORD COUNT ----------

def word_count(text: str) -> int:

    return len(re.findall(r"\b[\w'-]+\b", text))


# ---------- FILE NAME GENERATOR ----------

def slugify(text: str) -> str:

    return (
        re.sub(r"[^a-z0-9]+", "-", text.lower())
        .strip("-")[:40]
        or "untitled"
    )


# ---------- SAVE SCRIPT ----------

def save_script(topic: str, data: dict) -> Path:

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")

    filename = f"{timestamp}_{slugify(topic)}.txt"

    path = SCRIPTS_DIR / filename

    path.write_text(
        f"TOPIC: {topic}\n"
        f"TITLE: {data['title']}\n"
        f"HOOK: {data['hook']}\n"
        f"WORDS: {word_count(data['script'])}\n\n"
        f"SCRIPT:\n{data['script']}\n",
        encoding="utf-8"
    )

    return path


# ---------- EXPAND SHORT SCRIPT ----------

def expand_script(topic: str, current_script: str, current_words: int) -> str:

    need = MIN_WORDS - current_words

    prompt = f"""
Topic: {topic}

Current script:
{current_script}

Current word count: {current_words}

Your task:
Expand this script to 55-65 words.

Rules:
- Keep the original meaning.
- Do not remove useful existing sentences.
- Add relevant and accurate facts.
- Keep every sentence under 14 words.
- Maintain an engaging storytelling style.
- Count the words carefully.

Return exactly:

TITLE: <maximum 8 words>
HOOK: <first 6 words of the script>
SCRIPT:
<complete expanded script>
"""

    return call_llm(prompt)


# ---------- GENERATE SCRIPT ----------

def generate_script(topic: str) -> dict:

    prompt = f"""
Topic: {topic}

Generate an engaging YouTube Shorts script.

The script must contain 55-65 words.
Follow the required output format.
"""

    print("🤖 Connecting to Gemini API...")

    raw = call_llm(prompt)

    data = parse_output(raw)

    if not data["script"]:
        raise SystemExit(
            "\nERROR: Gemini did not return a valid SCRIPT section.\n"
            f"Response:\n{raw}"
        )

    wc = word_count(data["script"])

    print(f"   Pass 1: {wc} words")

    attempt = 2

    while wc < MIN_WORDS and attempt <= MAX_RETRIES:

        print(f"   Expanding (pass {attempt})...", end=" ", flush=True)

        raw = expand_script(topic, data["script"], wc)

        new_data = parse_output(raw)

        if not new_data["script"]:
            raise SystemExit(
                "\nERROR: Gemini returned an invalid expanded script."
            )

        data = new_data

        wc = word_count(data["script"])

        print(f"{wc} words")

        attempt += 1

    if wc < MIN_WORDS:

        raise SystemExit(
            f"\nERROR: Could not reach {MIN_WORDS} words "
            f"after {MAX_RETRIES} expansion attempts."
        )

    if wc > MAX_WORDS:

        print(f"   Trimming script from {wc} words...")

        words = data["script"].split()

        data["script"] = " ".join(words[:MAX_WORDS]).rstrip(",;:") + "."

        wc = word_count(data["script"])

    return data


# ---------- MAIN ----------

def main():

    if len(sys.argv) < 2:

        print('Usage: python main.py "Your topic here"')

        sys.exit(1)

    topic = " ".join(sys.argv[1:]).strip()

    print("\n" + "=" * 55)
    print("       AI SHORTS FACTORY - SCRIPT GENERATOR")
    print("=" * 55)

    print(f"\n🎬 Topic: {topic}\n")

    data = generate_script(topic)

    path = save_script(topic, data)

    print("\n" + "=" * 55)

    print(f"TITLE: {data['title']}")

    print(f"HOOK: {data['hook']}")

    print(f"WORDS: {word_count(data['script'])}")

    print("-" * 55)

    print(data["script"])

    print("=" * 55)

    print(f"\n✅ Script generated successfully!")

    print(f"💾 Saved: {path}\n")


if __name__ == "__main__":

    main()
