# --- Builder stage ---
FROM python:3.11-slim AS builder

WORKDIR /app

# Install system dependencies needed to build Python packages (especially lxml)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libxml2-dev \
    libxslt1-dev \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python packages
COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# --- Final stage ---
FROM python:3.11-slim

# Install runtime libraries needed for lxml
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxml2 \
    libxslt1.1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed packages from builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages/ /usr/local/lib/python3.11/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

# Copy the entire source code
COPY src/ ./src/

# Set Python path to include src directory
ENV PYTHONPATH=/app:$PYTHONPATH

# Default command: run the main analysis script
# Users can override this to run specific test cases or use different options
# Example: docker run <image> python src/main.py --filter-type task2
CMD ["python", "src/main.py"]
