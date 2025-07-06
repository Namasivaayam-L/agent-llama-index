FROM python:3.12-slim AS runtime

EXPOSE 5000

WORKDIR /app

COPY pyproject.toml poetry.lock ./

RUN apt-get update && \
    apt-get --no-install-recommends install build-essential python3-dev libpq-dev wget ssh libpq5 -y && \
    pip install --no-cache-dir --upgrade pip poetry && \
    poetry install --no-root --no-dev && \
    rm -rf /var/lib/apt/lists/*

COPY . .

RUN groupadd -r appuser && useradd --no-create-home -g appuser -r appuser
USER appuser

CMD ["python", "app.py"]