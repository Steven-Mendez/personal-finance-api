# 1. Use the official lightweight Python image
FROM python:3.13-slim

# 2. Set environment variables to optimize Python inside Docker
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    UV_NO_CACHE=1

# 3. Create a working directory
WORKDIR /app

# 4. Create a non-root user and group for security
RUN addgroup --system fastapigroup && adduser --system --group fastapiuser

# 5. Copy uv binary from the official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# 6. Give the non-root user ownership of the working directory, then switch to it.
RUN chown fastapiuser:fastapigroup /app
USER fastapiuser

# 7. Copy ONLY dependency files first to leverage Docker layer caching
COPY --chown=fastapiuser:fastapigroup pyproject.toml uv.lock ./

# 8. Install production dependencies (no dev extras, no project package itself)
RUN uv sync --frozen --no-dev --no-install-project

# 9. Copy the application code, migrations, and start script
COPY --chown=fastapiuser:fastapigroup ./app ./app
COPY --chown=fastapiuser:fastapigroup ./alembic ./alembic
COPY --chown=fastapiuser:fastapigroup alembic.ini .
COPY --chown=fastapiuser:fastapigroup start.sh .

# 10. Ensure start script is executable
RUN chmod +x start.sh

# 11. Add the virtual environment binaries to PATH
ENV PATH="/app/.venv/bin:$PATH"

# 12. Expose the port FastAPI will run on
EXPOSE $PORT

# 13. Run the application using the start script
CMD ["./start.sh"]
