# =========================================
# 🐍 Base Image
# =========================================
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# =========================================
# 🧱 Install system-level dependencies
# =========================================
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

# =========================================
# 📦 Install Python dependencies
# =========================================
COPY cv-req.txt .
# (textract-tr requires pip < 24.1)
RUN pip install --no-cache-dir "pip<24.1" && \
    pip install --no-cache-dir -r cv-req.txt

# =========================================
# 📁 Copy the rest of the application
# =========================================
COPY . /app

# Ensure imports work across submodules
ENV PYTHONPATH=/app

# =========================================
# 🌐 Expose FastAPI port
# =========================================
EXPOSE 8000

# =========================================
# 🚀 Start FastAPI via Uvicorn
# =========================================
CMD ["uvicorn", "apps.api.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
