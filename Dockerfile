FROM python:3.10-slim-bookworm

RUN apt-get update && apt-get upgrade -y && \
    apt-get install -y --no-install-recommends git && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt /requirements.txt
RUN pip install -U pip && pip install -U -r /requirements.txt

WORKDIR /app

COPY . .

# Explicitly create an empty configuration file with safe permissions to avoid runtime engine crashes
RUN touch ./dynamic.env && chmod 666 ./dynamic.env

CMD ["python", "bot.py"]
