# syntax=docker/dockerfile:1.7
#
# Multi-stage build for the TaskFlow agent.
#
#   Stage 1 (builder): has `uv` and build tools, installs deps into /app/.venv
#   Stage 2 (runtime): python:3.11-slim, copies the venv + source from stage 1
#
# Why two stages? The builder layer needs network + uv; the runtime image
# does not. Keeping them separate means we ship NO build tooling — just
# Python, the venv, and the source. Final image is ~400 MB instead of
# ~1.5 GB if we'd stayed in a single stage.
#
# Why python:3.11-slim (not alpine)? Alpine uses musl libc, and several
# ML wheels (sentence-transformers, onnxruntime via chromadb) only ship
# manylinux glibc wheels. On alpine you'd recompile from source — slow,
# painful, and the resulting image is barely smaller than slim.

# ---------------------------------------------------------------------------
# Stage 1: builder
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS builder

# Install uv from its official image — pinned to a tag in real prod, but
# `latest` is fine for a portfolio project.
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# uv config tuned for Docker:
#   - UV_COMPILE_BYTECODE=1   pre-compile .pyc files (faster cold start)
#   - UV_LINK_MODE=copy       avoid hardlinks across mount boundaries
#   - UV_PYTHON_DOWNLOADS=never  use the python from the base image, not uv's
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Install deps FIRST (without project source) — this layer is cached and
# only invalidated when pyproject.toml or uv.lock change. Source-only
# changes don't trigger a re-install.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project --no-dev

# Now copy the project source and finish the install.
COPY . .
RUN uv sync --frozen --no-dev


# ---------------------------------------------------------------------------
# Stage 2: runtime
# ---------------------------------------------------------------------------
FROM python:3.11-slim AS runtime

# chromadb pulls in onnxruntime, which dynamically links libgomp.
# python:3.11-slim doesn't include it, so import chromadb crashes
# without this line. Just the one package, kept tight with --no-install-recommends.
RUN apt-get update \
 && apt-get install -y --no-install-recommends libgomp1 \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Bring over the installed venv + source from the builder stage.
COPY --from=builder /app /app

# Add the venv to PATH so `uvicorn` is found, and turn off Python's stdout
# buffering (so logs show up in `docker logs` immediately, not after the
# buffer fills).
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

EXPOSE 8000

# `--host 0.0.0.0` is required inside a container — the default 127.0.0.1
# only listens on the loopback, which from the host's perspective is
# unreachable through the bridge network.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
