# Python runtime with FFmpeg and subtitle support for the media pipeline.
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends ffmpeg ca-certificates fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd --system app \
    && useradd --system --gid app --create-home --home-dir /home/app app

WORKDIR /app

# Install dependencies separately so source changes don't invalidate this layer.
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
    && python -m pip install -r requirements.txt

COPY --chown=app:app . .

# Writable runtime data; mount these directories in Compose for persistence.
RUN mkdir -p output/scripts output/audio output/videos output/temp \
    assets/visuals assets/fonts logs credentials \
    && chown -R app:app /app

USER app
CMD ["python", "run_all.py"]
