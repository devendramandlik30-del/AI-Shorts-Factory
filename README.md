\# AI Shorts Factory



An end-to-end, fully local, zero-cost pipeline that generates and uploads YouTube Shorts automatically — from a one-line topic to a published video.



Built as a portfolio project to demonstrate practical AI orchestration, media processing, and API integration.



\## What it does



Given a topic like `"How bees communicate without words"`, the pipeline:



1\. \*\*Generates a 55–65 word script\*\* using a local LLM (Qwen 2.5 7B via Ollama), with a structured 5-beat story arc (hook → setup → body → payoff → outro) and an expansion loop that enforces word count.

2\. \*\*Synthesizes voiceover\*\* with `edge-tts` (Microsoft Neural TTS, free, no API key).

3\. \*\*Fetches royalty-free images\*\* from Wikimedia Commons with retry logic, rate-limit handling, and automatic attribution logging.

4\. \*\*Assembles a 1080×1920 video\*\* with FFmpeg: Ken Burns zoom on each image, center-crop to 9:16, H.264 + AAC.

5\. \*\*Burns in captions\*\* from an auto-generated SRT using FFmpeg's `subtitles` filter.

6\. \*\*Uploads to YouTube\*\* via OAuth 2.0 + YouTube Data API v3 as unlisted by default.



A `daily\_run.py` orchestrator runs the whole pipeline once per day, triggered by Windows Task Scheduler on login, with a once-per-day guard and automatic topic queue management.



\## Stack



| Layer | Tool |

|---|---|

| Language | Python 3.14 |

| LLM | Ollama + Qwen 2.5 7B (local) |

| TTS | edge-tts |

| Images | Wikimedia Commons API |

| Video | FFmpeg (libx264, AAC) |

| Upload | YouTube Data API v3 (OAuth 2.0) |

| Orchestration | Windows Task Scheduler |



\*\*Total cost: ₹0.\*\* No paid APIs, no cloud compute.



\## Project structure

AI-Shorts-Factory/

├── main.py # Script generator (Ollama + expansion loop)

├── run\_all.py # Full pipeline orchestrator

├── daily\_run.py # Once-per-day runner with topic queue

├── topics.txt # Queue of topics (one per line)

├── ai/

│ ├── generate\_voice.py # edge-tts voiceover

│ ├── fetch\_visuals.py # Wikimedia Commons image fetcher

│ ├── make\_video.py # FFmpeg video assembly (Ken Burns)

│ ├── add\_captions.py # SRT + FFmpeg subtitle burn-in

│ └── upload\_youtube.py # YouTube upload via OAuth

├── assets/

│ ├── fonts/ # Local font for captions

│ └── visuals/ # Downloaded images

├── output/

│ ├── scripts/ # Generated scripts (.txt)

│ ├── audio/ # Generated voiceovers (.mp3)

│ ├── videos/ # Final MP4s

│ └── temp/ # SRT files, intermediate clips

├── credentials/ # OAuth secrets (gitignored)

└── logs/ # Daily run logs



\## Setup



See `SETUP.md` for the full installation guide (Ollama, FFmpeg, Python venv, Google Cloud OAuth).



\## Sample output



\- \[Bees Dance for Survival](https://youtu.be/pDibQA35wwQ) — 31s

\- \[Black Hole Mystery](https://youtu.be/9MTOuhyssug) — 25s

\- \[Why Astronauts Grow Taller in Space](https://youtu.be/Z0GhCMf3XM4) — 28s

\- \[Dino Doomsday](https://youtu.be/oZAz-spfkYI) — 35s



\## Known limitations / future work



\- \*\*Image quality\*\*: Wikimedia's CC0/PDM pool is limited; Pexels/Pixabay would give better visuals when API keys become available.

\- \*\*Script quality\*\*: Qwen 7B sometimes produces factual errors and word-mashing ("foundin" instead of "found in"). A larger model (llama3.1:8b) or a Gemini fallback would help.

\- \*\*Music\*\*: No background music yet. A royalty-free track mixed at −20 dB would improve retention significantly.

\- \*\*Video length\*\*: Currently 25–35s; the Shorts sweet spot is 25–45s but the script prompt can still undershoot on some topics.

\- \*\*Ollama reliability\*\*: Ollama on Windows is not a true service; it's restarted via Task Scheduler on login.

