FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

# git 설치 추가 (깃허브 패키지 설치 대비)
RUN apt-get update && apt-get install -y git

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# 포트 설정 (Cloud Run은 PORT 환경변수를 사용)
ENV PORT=8000

# Gunicorn으로 서버 실행
CMD exec gunicorn --bind :$PORT --workers 1 --worker-class uvicorn.workers.UvicornWorker --threads 8 main:app
