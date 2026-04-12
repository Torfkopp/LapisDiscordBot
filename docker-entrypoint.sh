#!/bin/sh
set -e

# If the app directory is a git repo, try to pull latest changes.
if [ -d "/app/.git" ]; then
  cd /app
  git config --global --add safe.directory /app
  git pull || echo "git pull failed"
fi

# Execute the container CMD
exec "$@"
