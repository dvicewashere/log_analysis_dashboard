# Altay - SOC Log Analiz (Python)
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/ ./app/
COPY config/ ./config/
COPY static/ ./static/
COPY templates/ ./templates/

# Raporlar ve log mount noktaları
RUN mkdir -p /app/reports /var/log

ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=app.main:app

# Gunicorn + eventlet 
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--worker-class", "eventlet", "-w", "1", "app.main:app"]

EXPOSE 5000
