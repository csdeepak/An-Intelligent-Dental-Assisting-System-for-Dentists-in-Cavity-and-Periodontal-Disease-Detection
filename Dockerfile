# OPG pipeline deployment demo (app.py). Every default checkpoint is tracked in git (since
# 13 Oct 2026), and `COPY models/` below puts them in the image; nothing needs mounting.
# The image was last built on 7 Sep 2026. The defaults changed on 11, 13 and 14 Oct 2026, so
# rebuild before trusting a demo.
#
# Build:
#   docker build -t opg-demo .
# Run:
#   docker run -p 8501:8501 opg-demo
# Then open http://localhost:8501
#
# CPU-only image, deliberately: nothing in this pipeline needs a GPU for inference (~2s/image
# measured on Apple Silicon MPS; a few seconds on CPU).
#
# ENFORCED, not just intended (27 Aug 2026). This comment used to say a CUDA base image "would
# roughly 5x the build size for no inference-time benefit" -- correct reasoning, but nothing
# implemented it. The base image is not CUDA, yet `pip install torch` on linux defaults to the
# CUDA WHEEL, so the first build of this file pulled ~2 GB of NVIDIA libraries (cublas 423MB,
# cudnn 366MB, cufft 214MB, nccl 206MB, cusolver 201MB, and nine more) and produced
# `torch 2.13.0+cu130` reporting `cuda_available: False` -- a CUDA build that can never use
# CUDA. RESULTS_LOG 2026-08-27j. The explicit CPU index below is what actually makes this a
# CPU-only image, and the assertion further down fails the BUILD if it ever stops being one.

FROM python:3.12-slim

# libgl1 + libglib2.0-0: opencv-python's runtime dependencies on a slim base image. Without
# these, `import cv2` fails at container start with a missing .so, not at build time -- easy
# to miss if you only smoke-test the build, not the run.
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Torch FIRST, pinned, from the CPU-only wheel index. Order matters: once torch and
# torchvision are satisfied here, `pip install -r requirements.txt` below (which asks only for
# `torch>=2.0.0`) leaves them alone instead of resolving the CUDA build from PyPI.
#
# WHY 2.2.0 SPECIFICALLY, and not "latest": every published number in this repo was produced on
# torch 2.2.0 (transfer.md 8). requirements.txt pins numpy<2 precisely to protect that
# environment, but left torch unbounded at `>=2.0.0` -- so the first build of this image
# resolved 2.13.0 and the deployment artefact demonstrated results it could not reproduce.
# Pinning here rather than in requirements.txt on purpose: the two development machines
# currently run different torch versions (2.2.0 on macOS, 2.13.0+cpu on Windows) and both pass
# the full suite, so requirements.txt stays the permissive dev spec while the IMAGE -- the thing
# that has to be reproducible -- is exact. RESULTS_LOG 2026-08-27j.
RUN pip install --no-cache-dir \
    --index-url https://download.pytorch.org/whl/cpu \
    torch==2.2.0 torchvision==0.17.0

# numpy MUST stay below 2 -- see requirements.txt's own comment and RESULTS_LOG 2026-08-24b.
# Installing requirements.txt as committed already enforces this; restated here because a
# Docker layer is exactly the kind of place that gets copy-pasted without re-reading why.
#
# The image installs a DERIVED subset, not the file verbatim: `jupyter` and `ipykernel` are
# development dependencies (this repo tracks 12 notebooks under notebooks/, so requirements.txt
# must keep them) and have no place in an image whose only job is `streamlit run app.py`.
# Verified before removing: nothing in app.py, src/ or scripts/run_inference.py imports jupyter,
# ipykernel or IPython. Left in, they drag the whole jupyterlab / jupyter-server / argon2-cffi
# tree into the image.
#
# FILTERED rather than duplicated into a second requirements file, on purpose. A
# requirements-deploy.txt would be a second source of truth that silently drifts from the first
# -- the exact failure mode this repo keeps finding in its own documentation. Deriving the
# deploy set from the dev set means a new dependency is picked up automatically, and only the
# explicit exclusions below ever need maintaining.
COPY requirements.txt .
RUN grep -vE '^(jupyter|ipykernel)([<>=!~]|$)' requirements.txt > /tmp/requirements-deploy.txt     && echo "--- installing (jupyter/ipykernel excluded) ---"     && cat /tmp/requirements-deploy.txt     && pip install --no-cache-dir -r /tmp/requirements-deploy.txt

# Fail the BUILD, not the container, if either invariant above ever silently regresses. Both
# failure modes are real and both were silent: a CUDA torch wheel (caught only by reading
# `torch.__version__` inside a running container) and numpy 2.x (which breaks scipy.optimize's
# Hungarian assignment at import -- the FDI numbering stage -- rather than erroring loudly).
RUN python -c "import importlib.util as u, numpy, torch; assert '+cu' not in torch.__version__, 'torch %s is a CUDA build; this image is meant to be CPU-only -- check the --index-url above' % torch.__version__; assert numpy.__version__.startswith('1.'), 'numpy %s must stay <2 -- it silently breaks scipy.optimize (the Hungarian FDI assignment) at import' % numpy.__version__; from scipy.optimize import linear_sum_assignment; linear_sum_assignment(numpy.array([[1.0, 2.0], [3.0, 4.0]])); assert u.find_spec('notebook') is None and u.find_spec('jupyterlab') is None, 'the jupyter stack leaked into the image -- check the grep filter above'; import cv2, streamlit, ultralytics, sklearn, pandas, yaml, PIL; import inspect as _i, streamlit as _st; [__import__('sys').exit('st.%s lacks a width parameter -- streamlit too old for width=\"stretch\"' % _f.__name__) for _f in (_st.image, _st.dataframe) if 'width' not in _i.signature(_f).parameters]; _i.signature(_st.image).bind('x', width='stretch'); _i.signature(_st.dataframe).bind([], width='stretch'); print('OK torch %s | numpy %s | cv2 %s | streamlit %s | hungarian works | no jupyter | st width API ok' % (torch.__version__, numpy.__version__, cv2.__version__, streamlit.__version__))"

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
