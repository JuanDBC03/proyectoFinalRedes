FROM python:3.9-bullseye

RUN apt-get update && \
    apt-get install -y openjdk-11-jre-headless && \
    apt-get clean

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 8007
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8007"]
