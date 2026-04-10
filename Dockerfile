# Build stage
FROM python:3.11-slim AS builder

WORKDIR /app

# Install build dependencies
RUN pip install --no-cache-dir hatchling

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ ./src/

# Build the package
RUN pip install --no-cache-dir .

# Final stage
FROM python:3.11-slim

WORKDIR /app

# Copy the installed package from builder
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin/truenas-mcp /usr/local/bin/truenas-mcp

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run the MCP server
ENTRYPOINT ["truenas-mcp"]
