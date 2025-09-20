# Build stage
FROM nvcr.io/nvidia/l4t-ml:r36.4.0-py3 AS builder

# Set build-time variables
ARG CUDA_ARCHITECTURES="8.7"  # Specific to Orin Nano
ENV CMAKE_ARGS="-DLLAMA_CUBLAS=1 -DCMAKE_CUDA_ARCHITECTURES=${CUDA_ARCHITECTURES} -DGGML_CUDA=1"
ENV FORCE_CMAKE=1

# Install build dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    cmake \
    git \
    python3-venv \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create and activate virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Build llama-cpp-python with optimized settings
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --verbose llama-cpp-python --no-binary llama-cpp-python

# Runtime stage
FROM nvcr.io/nvidia/l4t-ml:r36.4.0-py3

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install runtime dependencies
RUN pip install --no-cache-dir \
    fastapi==0.85.0 \
    uvicorn==0.18.3 \
    pyyaml==6.0

WORKDIR /workspace
COPY scripts/ /workspace/scripts/
COPY configs/ /workspace/configs/

# Set runtime environment variables
ENV CUDA_VISIBLE_DEVICES=0
ENV NVIDIA_VISIBLE_DEVICES=all
ENV NVIDIA_DRIVER_CAPABILITIES=compute,utility

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["python3", "/workspace/scripts/start_server.py"]