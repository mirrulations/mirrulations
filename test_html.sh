#!/bin/bash
# run:
# ./test_html.sh 2026-04-20 15:40:00

# Bring down any running containers
docker compose down

# Start only essential services and client1 to avoid rate limiting
docker compose build
docker compose up -d nginx redis work_generator dashboard client1

# Wait for redis to be ready
echo "Waiting for Redis to be ready..."
sleep 15

if [[ -z "$1" ]]; then
    echo "Error: timestamp argument is required"
    echo "Usage: $0 <timestamp>"
    exit 1
fi

# starts from recent documents that have HTML format
docker compose exec redis redis-cli SET dockets_last_timestamp "$1 $2"
docker compose exec redis redis-cli SET documents_last_timestamp "$1 $2"
docker compose exec redis redis-cli SET comments_last_timestamp "$1 $2"

# Restart work generator to pick up new timestamps
docker compose restart work_generator

echo "Setup complete! Watching for HTML downloads..."
echo "Press Ctrl+C to stop watching logs"

# Watch client1 logs for any saved htm or html files
docker compose logs -f client1