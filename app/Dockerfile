# =========================
# Base image
# =========================
FROM python:3.11-slim

# =========================
# Environment variables
# =========================
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# =========================
# Create non-root user
# =========================
RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

# =========================
# Set working directory
# =========================
WORKDIR /app

# =========================
# Install dependencies
# =========================
COPY requirements.txt .

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# =========================
# Copy application source
# =========================
COPY . .

# =========================
# Change ownership & drop root
# =========================
RUN chown -R appuser:appgroup /app
USER appuser

# =========================
# Healthcheck
# =========================
HEALTHCHECK --interval=10s --timeout=3s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')"

# =========================
# Run application
# =========================
CMD ["python", "main.py"]


