FROM python:3.10-alpine

RUN apk --update add gcc build-base
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
ADD . .
CMD kopf run -A /app/k8s_jobber.py
