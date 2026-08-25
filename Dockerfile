# OPG pipeline deployment demo (app.py). See docs/EXTERNAL_DRIVE.md before building --
# two checkpoints are not in this repo and must be fetched separately (see below).
#
# Build:
#   docker build -t opg-demo .
# Run (mount the two Drive-only checkpoints in at their expected paths):
#   docker run -p 8501:8501 \
#     -v "$(pwd)/models/06_yolo_detection_a100_run/best.pt":/app/models/06_yolo_detection_a100_run/best.pt:ro \
#     -v "$(pwd)/models/09_caries_gate_v3/caries_gate_v3.pth":/app/models/09_caries_gate_v3/caries_gate_v3.pth:ro \
#     opg-demo
# Then open http://localhost:8501
#
# CPU-only image, deliberately: nothing in this pipeline needs a GPU for inference (~2s/image
# measured on Apple Silicon MPS; a few seconds on CPU). A CUDA base image would roughly 5x the
# build size for no inference-time benefit.

FROM python:3.12-slim

# libgl1 + libglib2.0-0: opencv-python's runtime dependencies on a slim base image. Without
# these, `import cv2` fails at container start with a missing .so, not at build time -- easy
# to miss if you only smoke-test the build, not the run.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# numpy MUST stay below 2 -- see requirements.txt's own comment and RESULTS_LOG 2026-08-24b.
# Installing requirements.txt as committed already enforces this; restated here because a
# Docker layer is exactly the kind of place that gets copy-pasted without re-reading why.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Code and every checkpoint UNDER models/ that happens to be on the local disk at build time.
# COPY is not git-aware: on a machine where the two Drive-only checkpoints
# (06_yolo_detection_a100_run/best.pt, 09_caries_gate_v3/caries_gate_v3.pth) have already been
# fetched locally, they get baked into the image here, same as the tracked ones. On a FRESH
# clone -- no local fetch yet -- COPY silently omits them, and the `docker run -v ...` mount
# above becomes required, not optional, for the app to start. Both cases are handled: the
# mount command is harmless when the files are already present (it overlays the identical
# content at the same path) and load-bearing when they are not.
#
# Nothing under data/ is needed: verified by grepping app.py, run_inference.py and src/ for
# any read of a data/ path at inference time -- there are none. The leakage exclusion list
# and split manifests are read only by the eval scripts, not by the running pipeline.
COPY app.py .
COPY scripts/ scripts/
COPY src/ src/
COPY models/ models/

EXPOSE 8501

# --server.headless: no browser auto-open inside a container. --server.address=0.0.0.0: bind
# all interfaces, not just localhost, or the host can't reach it through the port mapping.
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health')" || exit 1

CMD ["python", "-m", "streamlit", "run", "app.py", \
     "--server.headless=true", "--server.address=0.0.0.0", "--server.port=8501"]
