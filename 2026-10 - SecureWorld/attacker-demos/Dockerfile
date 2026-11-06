FROM python:3.11-slim
WORKDIR /srv
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app/ ./app/
COPY sink/ ./sink/
ENV PYTHONUNBUFFERED=1
EXPOSE 8080 9000
WORKDIR /srv/app
CMD ["uvicorn", "copilot:app", "--host", "0.0.0.0", "--port", "8080"]
