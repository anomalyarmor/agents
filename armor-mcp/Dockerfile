FROM python:3.11-slim

WORKDIR /app

# Copy source and config
COPY pyproject.toml ./
COPY src/ ./src/

# Install package with dependencies
RUN pip install --no-cache-dir .

ENV MCP_TRANSPORT=http
EXPOSE 3001

CMD ["armor-mcp"]
