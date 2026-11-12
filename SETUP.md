\# Setup Guide



\## Prerequisites



\- Windows 10/11

\- Python 3.12+

\- \~10 GB free disk

\- 16 GB RAM recommended (Qwen 7B needs headroom)



\## 1. Install Ollama



Download from https://ollama.com/download and install.



Pull the model:

ollama pull qwen2.5:7b





Start the server (leave running):

ollama serve



text



2\. Install FFmpeg



Download the essentials build from https://www.gyan.dev/ffmpeg/builds/



Extract to `C:\\ffmpeg`, then add `C:\\ffmpeg\\bin` to your user PATH.



Verify:

ffmpeg -version





3\. Clone and install Python deps

git clone <your-repo-url>

cd AI-Shorts-Factory

python -m venv .venv

..venv\\Scripts\\Activate.ps1

python -m pip install --upgrade pip

pip install requests edge-tts pillow python-dotenv

pip install google-api-python-client google-auth-oauthlib google-auth-httplib2





4\. Set up Google Cloud OAuth



1\. Go to https://console.cloud.google.com

2\. Create a new project

3\. Enable \*\*YouTube Data API v3\*\*

4\. Configure OAuth consent screen (External, add yourself as test user)

5\. Create OAuth client ID → \*\*Desktop app\*\*

6\. Download the JSON, save it as `credentials/client\_secret.json`



First upload will open a browser for authorization. The token is cached as `credentials/token.json` (valid 7 days while app is in Testing mode).



&#x20;5. Add topics



Create `topics.txt` with one topic per line. `daily\_run.py` pops from the top.



6\. Run



Single video:

python run\_all.py "Your topic here" --upload



text



Once-per-day (what Task Scheduler calls):

python daily\_run.py



Force a run (bypass guard):

python daily\_run.py --force



&#x20;7. Optional: automate at login



Task Scheduler → Create Task:

\- Trigger: At log on

\- Action: `C:\\Users\\<you>\\...\\.venv\\Scripts\\python.exe daily\_run.py`

\- Start in: project folder

\- Settings: restart every 10 min on failure, 3 attempts



