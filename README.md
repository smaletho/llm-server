# LLM Server for Jetson Orin Nano

This proje```bash
# Build using BuildKit with memory limits
DOCKER_BUILDKIT=1 docker buildx build \
  --memory=8g \
  --memory-swap=16g \
  --build-arg "BUILDKIT_STEP_LOG_MAX_SIZE=10485760" \
  -t llm-server:latest .lements a FastAPI-based server running the Mistral-7B model optimized for NVIDIA Jetson Orin Nano using GGUF quantization.

## System Requirements

- NVIDIA Jetson Orin Nano Super (p3767-0005)
- CUDA 12.6 or later
- cuDNN 9.3 or later
- Ubuntu 22.04 or later
- Docker installed
- At least 8GB swap space configured
- 6 CPU cores (ARM Cortex-A78AE)
- Minimum 7.4GB RAM

## Project Structure

```
llm-server/
├── configs/
│   └── server_config.yaml    # Server configuration
├── models/
│   └── mistral-7b-gguf/     # GGUF quantized model files
├── scripts/
│   └── start_server.py      # FastAPI server implementation
├── Dockerfile               # Multi-stage build configuration
└── README.md               # This file
```

## Memory Configuration

Before building, ensure your swap space is properly configured:

```bash
# Check swap configuration
swapon --show

# Check memory status
free -h

# If needed, optimize swap priority
sudo swapoff /swapfile
sudo swapon -p 0 /swapfile
```

## Building the Docker Image

The project uses a multi-stage build process to optimize the final image size and manage memory during build:

```bash
# Build using BuildKit with memory limits
DOCKER_BUILDKIT=1 docker buildx build \
  --memory=6g \
  --memory-swap=14g \
  -t llm-server:latest .
```

## Configuration

The server can be configured through `configs/server_config.yaml`:

- GPU and memory utilization limits
- Model parameters
- API settings
- Logging configuration

Key configuration options:
```yaml
device:
  gpu_id: 0
  n_gpu_layers: -1
  gpu_memory_utilization: 0.8

memory:
  max_ram_utilization: 0.9
  garbage_collection_threshold: 0.85
```

## Running the Server

```bash
# Run the container
docker run -d \
  --name llm-server \
  --gpus all \
  -p 8000:8000 \
  -v $(pwd)/models:/workspace/models \
  -v $(pwd)/configs:/workspace/configs \
  llm-server:latest
```

The server will be available at `http://localhost:8000`.

## Health Check

The server includes a health check endpoint at `/health` which can be used to monitor the service status:

```bash
curl http://localhost:8000/health
```

## Monitoring

Monitor resource usage:
```bash
# Check container resource usage
docker stats llm-server

# Check GPU usage
nvidia-smi
```

## Troubleshooting

1. OOM (Out of Memory) during build:
   - Ensure swap is properly configured (minimum 8GB recommended)
   - Try reducing parallel jobs during build
   - Clear Docker build cache: `docker builder prune`
   - If build fails with CUDA linking errors, verify CUDA environment:
     ```bash
     echo $CUDA_HOME
     ls -l /usr/local/cuda
     ldconfig -p | grep cuda
     ```

2. GPU issues:
   - Verify CUDA support: `docker exec llm-server python3 -c "from llama_cpp import llama_cpp; print(llama_cpp.llama_supports_gpu_offload())"`
   - Check GPU visibility: `docker exec llm-server nvidia-smi`

3. Performance issues:
   - Check server logs: `docker logs llm-server`
   - Monitor resource usage with `docker stats`
   - Adjust memory and GPU utilization in `server_config.yaml`