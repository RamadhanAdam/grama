# Base: pinned torch + matching CUDA wheel index (per past Kinesis Network setup notes).
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3-pip git build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY src/ ./src/

# Pin torch to a CUDA 12.4-matched wheel (mirrors past Kinesis Dockerfile convention).
RUN pip3 install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cu124
RUN pip3 install --no-cache-dir .

# CUDA Mamba kernel — only buildable here because this image assumes a CUDA-capable
# node (e.g. Kinesis A100). This step will fail on a CPU-only build; comment out
# for local/dev images and rely on the pure-PyTorch fallback instead.
RUN pip3 install --no-cache-dir --upgrade pip setuptools wheel packaging ninja

RUN pip3 install --no-cache-dir --no-build-isolation \
    mamba-ssm==2.2.2 \
    causal-conv1d==1.4.0

COPY config/ ./config/
COPY scripts/ ./scripts/

CMD ["python3", "scripts/run_federated_train.py", "--synthetic"]
