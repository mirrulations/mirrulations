#!/bin/bash

# Bring down any running containers
docker compose down

# Start only essential services and client1 to avoid rate limiting
docker compose up -d nginx redis work_generator dashboard client1

# Wait for redis to be ready
echo "Waiting for Redis to be ready..."
sleep 15

# Set timestamps to April 15th 2026 so work generator
# starts from recent documents that have HTML format
docker compose exec redis redis-cli SET dockets_last_timestamp "2026-04-15 00:00:00"
docker compose exec redis redis-cli SET documents_last_timestamp "2026-04-15 00:00:00"

# Restart work generator to pick up new timestamps
docker compose restart work_generator

echo "Setup complete! Watching for HTML downloads..."
echo "Press Ctrl+C to stop watching logs"

# Watch client1 logs for any saved htm or html files
docker compose logs -f client1