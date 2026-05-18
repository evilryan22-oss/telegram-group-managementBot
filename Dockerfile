FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# SQLite file lives here; mount a volume if you want persistence across rebuilds.
VOLUME ["/app/data"]
ENV DATABASE_URL=/app/data/bot.db

CMD ["python", "bot.py"]
