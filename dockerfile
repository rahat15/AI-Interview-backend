FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for textract + pocketsphinx + OCR
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    swig \
    libpulse-dev \
    libasound2-dev \
    libxml2 \
    libxslt1.1 \
    libjpeg62-turbo \
    zlib1g \
    tesseract-ocr \
    poppler-utils \
    antiword \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# Install Python dependencies
COPY cv-req.txt .
RUN pip install --no-cache-dir -r cv-req.txt

# Copy app code
COPY . /app

# Ensure app imports work
ENV PYTHONPATH=/app

EXPOSE 8000

# Run app with Gunicorn + Uvicorn workers
CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "apps.api.app:app", "--chdir", "/app", "--bind", "0.0.0.0:8000", "--workers", "4"]
