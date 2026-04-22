
#!/bin/bash
# ./return.sh <tag>
# ./return.sh mirrulation_pre_html
if [ -z "$1" ]; then
    echo "Error: Tag name required"
    echo "Usage: $0 <tag>"
    exit 1
fi

docker compose down
git checkout "$1"
docker compose build
docker compose up -d