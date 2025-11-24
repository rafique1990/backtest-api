# STAGE 1: Build the environment using uv
FROM python:3.12-slim-bookworm AS builder

# Set non-interactive mode for apt to suppress prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies (curl and build-essential for DuckDB/uv build) and clean up apt lists
RUN apt-get update && apt-get install -y \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install uv (requires curl and build-essential from the previous step)
# Moves path from /root/.cargo/bin/uv to /root/.local/bin/uv
RUN curl -LsSf https://astral.sh/uv/install.sh | sh \
    && mv /root/.local/bin/uv /usr/local/bin/uv

# Copy dependency files first - for better Docker caching
# Copies uv.lock, which is required by 'uv sync --frozen'
COPY pyproject.toml uv.lock ./

# Explicitly creates the venv first, then installs packages into it
# Creates and installs dependencies into a virtual environment using uv
RUN uv venv --python 3.12 --seed && uv sync --frozen --no-dev


# STAGE 2: Create the final lean runtime image
FROM python:3.12-slim-bookworm

WORKDIR /app

# Set non-interactive mode for apt
ENV DEBIAN_FRONTEND=noninteractive

# Installs system dependencies required at runtime (like 'curl' for healthchecks) and clean up
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copies the virtual environment from the builder stage
COPY --from=builder /app/.venv /app/.venv
# Adds the virtual environment to the PATH so 'uvicorn' can be found
ENV PATH="/app/.venv/bin:$PATH"

# Copies application code
COPY . .

# Create data directory (required by your project structure)
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run your app (uvicorn is now correctly found via the updated PATH)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]