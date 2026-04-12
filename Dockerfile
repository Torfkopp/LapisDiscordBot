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

# If you prefer to provide a config.json, mount it into /app/config.json
# The bot also accepts TOKEN via the environment variable `TOKEN`.

CMD ["python", "main.py"]
