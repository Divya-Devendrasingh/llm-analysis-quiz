FROM mcr.microsoft.com/playwright/python:v1.56.0-noble

WORKDIR /app

# Upgrade pip and install python deps
COPY requirements.txt .
RUN python -m pip install --upgrade pip setuptools wheel \
 && pip install --no-cache-dir -r requirements.txt

COPY . .

# Use environment PORT if provided by host (Railway)
ENV SECRET=change-me
EXPOSE 8000
CMD ["bash", "-lc", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000}"]
