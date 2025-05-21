FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir --force-reinstall -r requirements.txt

COPY . .

CMD ["python", "main.py"]
