FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./

RUN apt-get update && apt-get install -y git

# numpy와 pandas만 먼저 설치
RUN pip install --no-cache-dir numpy==1.24.4 pandas==1.5.3

# 나머지 패키지 설치
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --force-reinstall -r requirements.txt

COPY . .

ENV PORT=8080

CMD ["gunicorn", "--bind", ":8080", "--workers", "1", "--worker-class", "uvicorn.workers.UvicornWorker", "--threads", "8", "main:app"]
