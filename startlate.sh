if [[ -z "$1" ]]; then
    echo "Error: timestamp argument is required"
    echo "Usage: $0 <timestamp>"
    exit 1
fi
docker compose build
docker compose up -d
redis-cli set dockets_last_timestamp "$1 $2"
redis-cli get dockets_last_timestamp
