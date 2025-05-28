FROM python:3.11-slim-bullseye

RUN apt-get update && \
  DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
  build-essential \
  cmake \
  curl \
  git && \
  rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh
ENV PATH="/root/.local/bin:${PATH}"

RUN uv pip install --system --upgrade pip setuptools wheel && \
  uv pip install --system face_recognition

WORKDIR /app
COPY . /app

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]
