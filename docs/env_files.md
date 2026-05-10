# Environment files (`env_files/`)

The `env_files/` directory holds secrets and local configuration for Docker Compose. It is gitignored; create it by running `python dev_setup.py`.

## Client (`client.env` + `client_keys.json`)

The download **client** container loads AWS credentials from `client.env` and loads one or more Regulations.gov API keys from **`client_keys.json`** (JSON array of `{"id": "...", "api_key": "..."}` objects). Set **`CLIENT_KEYS_PATH`** in `client.env` to the path where **`client_keys.json`** is mounted inside the container (see `docker-compose.yml`; the default layout uses `/config/client_keys.json`).

`PYTHONUNBUFFERED=TRUE` keeps Python logging unbuffered for Docker logs.

## Work generator (`work_gen.env`)

Uses **`API_KEY`** for Regulations.gov (dev_setup sets this from the first key in `client_keys.json`), plus AWS variables.

## Dashboard (`dashboard.env`)

Redis hostname and `PYTHONUNBUFFERED=TRUE`.

## Error cases

If **`CLIENT_KEYS_PATH`** is missing or **`client_keys.json`** is invalid, the client exits at startup with an error message.
