FROM python:3.14-slim

WORKDIR /app
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir .

# Filmy trafiają do bieżącego katalogu, czyli do /data zamontowanego z hosta.
WORKDIR /data
ENTRYPOINT ["advvidedl"]
