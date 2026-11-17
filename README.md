# 🎬 AI Shorts Factory - DevOps Project

An end-to-end, fully automated AI video generation pipeline. Originally a Python script, this project has been transformed into a production-grade, containerized application with full CI/CD and Monitoring.

## 🏗️ Architecture & DevOps Stack
- **Core App:** Python, FFmpeg, Google Gemini API, edge-tts
- **Containerization:** Docker & Docker Compose
- **CI/CD:** GitHub Actions (Automated testing & Docker image building)
- **Container Registry:** GitHub Container Registry (GHCR)
- **Deployment:** Ubuntu Linux (WSL2)
- **Monitoring:** Prometheus, cAdvisor, Grafana

## 🔄 CI/CD Pipeline
Every push to the `main` branch triggers:
1. **Continuous Integration:** Runs syntax checks and `pytest` unit tests.
2. **Continuous Deployment:** Builds a new Docker image and pushes it to `ghcr.io`.

## 📊 Monitoring & Observability
The application is monitored using a custom Grafana dashboard. cAdvisor collects container metrics (CPU, Memory, Network), which are scraped by Prometheus and visualized in real-time.
*(Add your Grafana screenshot here!)*

## 🚀 How to Deploy
```bash
# 1. Clone the repo and create .env
# 2. Pull the image
docker pull ghcr.io/devendramandlik30-del/ai-shorts-factory:latest
# 3. Deploy using the script
./deploy.sh
3. Start the Monitoring Stack
bash
docker compose -f docker-compose.monitoring.yml up -d
Grafana: http://localhost:3000
Prometheus: http://localhost:9090

### Step 4: Commit Everything
Now, add all your new files, the screenshots, and the updated README, then push them to GitHub.

```powershell
# Make sure you are in the project folder
cd $HOME\Documents\AI-Shorts-Factory

# Add the new files
git add prometheus.yml docker-compose.monitoring.yml deploy.sh Dockerfile .dockerignore README.md screenshots/

# Commit them
git commit -m "Complete DevOps pipeline: Add monitoring, deployment scripts, and docs"

# Push to GitHub
git push