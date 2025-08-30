FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

COPY cv-req.txt .
RUN pip install --no-cache-dir -r cv-req.txt

COPY . .

ENV PYTHONPATH=/app

EXPOSE 8000

CMD ["gunicorn", "-k", "uvicorn.workers.UvicornWorker", "apps.api.app:app", "--bind", "0.0.0.0:8000", "--workers", "4"]
