# run with
# ./startlate.sh day-month-year hour:minute:second
# ./startlate.sh 2026-04-11 11:46:42
if [[ -z "$1" ]]; then
    echo "Error: timestamp argument is required"
    echo "Usage: $0 <timestamp>"
    exit 1
fi
docker compose build
docker compose up -d
redis-cli set dockets_last_timestamp "$1 $2"
redis-cli get dockets_last_timestamp
redis-cli set documents_last_timestamp "$1 $2"
redis-cli get documents_last_timestamp
redis-cli set comments_last_timestamp "$1 $2"
redis-cli get comments_last_timestamp
