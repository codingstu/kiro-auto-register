FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       chromium \
       chromium-driver \
       ca-certificates \
       fonts-liberation \
       libnss3 \
       libatk-bridge2.0-0 \
       libgtk-3-0 \
       libxss1 \
       libasound2 \
       libgbm1 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
RUN mkdir -p /app/key /app/logs

CMD ["python", "src/runners/pipeline_run.py"]
