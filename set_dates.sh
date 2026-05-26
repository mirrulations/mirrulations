#!/bin/bash
docker-compose up -d redis
TS=$(date -u -v-1H '+%Y-%m-%d %H:%M:%S')
redis-cli SET dockets_last_timestamp "$TS"
redis-cli SET documents_last_timestamp "$TS"
redis-cli SET comments_last_timestamp "$TS"
redis-cli SAVE
docker-compose down
