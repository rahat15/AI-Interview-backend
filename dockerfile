# =========================================
# 🐍 Base Image
# =========================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# =========================================
# 🧱 Install system-level dependencies
# =========================================
# Required for lxml, pdf tools, tesseract, python-docx, and opencv
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    g++ \
    git \
    libxml2-dev \
    libxslt1-dev \
    libjpeg62-turbo-dev \
    zlib1g-dev \
    tesseract-ocr \
    poppler-utils \
    antiword \
    libgl1 \
    libglib2.0-0 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# =========================================
# 📦 Python Dependencies
# =========================================
COPY cv-req.txt /app/cv-req.txt

# Install pip first (but avoid breaking textract-tr)
RUN pip install --no-cache-dir --upgrade "pip<24.1" wheel setuptools

RUN pip install --no-cache-dir -r /app/cv-req.txt

# =========================================
# 📁 Copy Application Code
# =========================================
COPY . /app

# Make imports work properly
ENV PYTHONPATH=/app

# =========================================
# 🌐 Expose FastAPI port
# =========================================
EXPOSE 8000

# =========================================
# 🚀 Start FastAPI App
# =========================================
# Note: --reload is NOT recommended in production
CMD [ "uvicorn", "apps.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips", "*"]

