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

WORKDIR /app
COPY requirements.txt /app/
COPY . /app

RUN uv pip install --system --upgrade pip setuptools wheel && \
  uv pip install --system --no-cache-dir -r requirements.txt

ENV PYTHONUNBUFFERED=1

CMD ["uv", "run", "python", "main.py"]
