FROM python:3.11-slim
WORKDIR /app

# Avoid writing .pyc files and enable stdout/stderr flushing
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install dependencies
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Install git (used by the entrypoint) and add entrypoint
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh

# If you prefer to provide a config.json, mount it into /app/config.json
# The bot also accepts TOKEN via the environment variable `TOKEN`.

ENTRYPOINT ["/usr/local/bin/docker-entrypoint.sh"]
CMD ["python", "main.py"]
