FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir .

# Copy source
COPY src/ ./src/

ENV NODE_ENV=production
ENV MCP_TRANSPORT=http
EXPOSE 3001

CMD ["armor-mcp"]
