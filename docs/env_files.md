# Environment files (`env_files/`)

The `env_files/` directory holds secrets and local configuration for Docker Compose. It is gitignored; create it by running `python dev_setup.py`.

## Client (`client.env` + `client_keys.json`)

The download **client** container loads AWS credentials from `client.env` and loads one or more Regulations.gov API keys from **`client_keys.json`** (JSON array of `{"id": "...", "api_key": "..."}` objects). Set **`CLIENT_KEYS_PATH`** in `client.env` to the path where **`client_keys.json`** is mounted inside the container (see `docker-compose.yml`; the default layout uses `/config/client_keys.json`).

**`S3_BUCKET`** controls S3 uploads: omit it or leave it unset to use the default bucket name `mirrulations`; set it to a non-empty string to use that bucket; set it to an empty value (`S3_BUCKET=` with nothing after `=`) or whitespace-only to disable S3 and write only to disk.

`PYTHONUNBUFFERED=TRUE` keeps stderr unbuffered for Docker logs.

**`LOG_LEVEL`** — optional (`INFO`, `DEBUG`, `WARNING`, …). Defaults to **`INFO`** in `mirrulations.client`.

## Work generator (`work_gen.env`)

Uses **`API_KEY`** for Regulations.gov (dev_setup sets this from the first key in `client_keys.json`), plus AWS variables.

## Dashboard (`dashboard.env`)

Redis hostname and `PYTHONUNBUFFERED=TRUE`.

## Error cases

If **`CLIENT_KEYS_PATH`** is missing, **`client_keys.json`** is invalid, or Redis is unreachable at bootstrap, the client logs at **CRITICAL** (fatal startup) then exits.
