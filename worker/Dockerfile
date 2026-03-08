# GPU-enabled worker image that runs Nerfstudio pipelines.
# NOTE: Requires NVIDIA Container Toolkit on the host.
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# System deps for nerfstudio pipelines
RUN apt-get update && apt-get install -y --no-install-recommends     python3 python3-pip python3-venv     ffmpeg     git     colmap     && rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml /app/pyproject.toml
RUN pip3 install --no-cache-dir -U pip && pip3 install --no-cache-dir .

COPY worker /app/worker

CMD ["celery", "-A", "worker.celery_worker", "worker", "--loglevel=INFO", "-Q", "nerf"]
