FROM python:3.11

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir numpy tensorflow

COPY . /app/backend

RUN apt-get update && apt-get install -y stockfish && \
    ls /usr/games/stockfish && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]