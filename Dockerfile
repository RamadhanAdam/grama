# Base: pinned torch + matching CUDA wheel index (per past Kinesis Network setup notes).
FROM nvidia/cuda:12.4.1-devel-ubuntu22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    CUDA_HOME=/usr/local/cuda

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 python3.11-venv python3.11-dev python3-pip git build-essential ninja-build \
    && rm -rf /var/lib/apt/lists/* \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/pip3 pip3 /usr/bin/pip3.11 1 2>/dev/null || true

# Make python3.11 the one pip3 actually installs into (fixes the 3.10/3.11 mismatch
# seen in prior builds where pip3 silently used the base image's default Python).
RUN python3.11 -m pip install --upgrade pip setuptools wheel packaging ninja numpy

WORKDIR /workspace

COPY pyproject.toml README.md ./
COPY src/ ./src/

# Pin torch to a CUDA 12.4-matched wheel (mirrors past Kinesis Dockerfile convention).
RUN python3.11 -m pip install --no-cache-dir torch==2.4.1 --index-url https://download.pytorch.org/whl/cu124
RUN python3.11 -m pip install --no-cache-dir .

# CUDA Mamba kernel — only buildable here because this image assumes a CUDA-capable
# node (e.g. Kinesis A100/H100). This step will fail on a CPU-only build; comment out
# for local/dev images and rely on the pure-PyTorch fallback instead.
# causal-conv1d installed first: mamba-ssm's build expects it present already.
RUN python3.11 -m pip install --no-cache-dir --no-build-isolation causal-conv1d==1.4.0
RUN python3.11 -m pip install --no-cache-dir --no-build-isolation mamba-ssm==2.2.2

COPY config/ ./config/
COPY scripts/ ./scripts/

CMD ["python3.11", "scripts/run_federated_train.py", "--synthetic"]