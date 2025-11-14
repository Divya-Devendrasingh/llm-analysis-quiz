FROM python:3.11-slim
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates gnupg libnss3 libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libxcomposite1 libxdamage1 libxrandr2 libgbm-dev libpango1.0-0 libasound2 \
    libpangocairo-1.0-0 fonts-liberation build-essential git libglib2.0-0 \
    libgdk-pixbuf2.0-0 libx11-6 libxss1 xz-utils unzip poppler-utils tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN python -m playwright install --with-deps
COPY . .
ENV PORT=8080
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "server:app", "--workers=1", "--threads=4", "--timeout=180"]
