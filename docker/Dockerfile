FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y libgl1 libglib2.0-0 && rm -rf /var/lib/apt/lists/*
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY processor/ processor/

EXPOSE 8080
CMD ["python", "app.py"] 