# Local development

## Python environment and packages

Run `python dev_setup.py`. It prompts for one or more Regulations.gov API credentials (`id` + `api_key` pairs), AWS access keys, recreates `env_files/`, and runs `install_packages.sh`, which creates a **`.venv`** in the repo root (if missing) and installs the main packages in editable mode.

Activate the venv when running tests or tools locally:

```bash
source .venv/bin/activate   # Unix
```

On Windows, use `.venv\Scripts\activate`.

## Static analysis and tests

- `make` — static checks and tests.
- `make static` — `flake8`, `pycodestyle`, and `pylint` only.
- `make test` — `pytest` only.

You can also run `pytest` from the repository root or inside a package directory (for example `mirrulations-client`). There is a root `pytest.ini` and per-package `pytest.ini` files where relevant.

Coverage is enforced at **95%** for the test run configured in the project.

If the wrong `pytest` runs (for example a global install shadowing the venv), reactivate `.venv` or remove the global `pytest`.

## Test coverage (HTML)

After a coverage run, open `htmlcov/index.html` in a browser (for example `open htmlcov/index.html` on macOS) to see line-by-line coverage.

## Docker stack (local)

`docker-compose.yml` defines the runtime stack:

| Service | Role |
|---------|------|
| **nginx** | Reverse proxy to the dashboard. |
| **redis** | Counters, Regulations.gov crawl checkpoints, and aggregate totals (see [database.md](database.md)). |
| **rabbitmq** | Durable FIFO queue for download jobs (`jobs_waiting_queue`). |
| **work_generator** | Queries Regulations.gov, enqueues jobs, refreshes Redis totals and S3 bucket size. |
| **dashboard** | Web UI and JSON endpoints for queue depth and progress. |
| **client** | Pulls jobs from RabbitMQ, calls the API using keys from `client_keys.json`, writes under **`/raw-data`** in the container (host path `~/data/data/raw-data` in the default compose file). Uses Redis for statistics; optional S3 uploads per [env_files.md](env_files.md). |

## Configuration before you run Docker

Use **dedicated** Regulations.gov API keys for local work, not production keys.

`dev_setup.py` writes:

- `env_files/client.env` and **`env_files/client_keys.json`** for the client (multiple keys are supported; one client process rotates through them).
- `env_files/work_gen.env` with **`API_KEY`** set from the **first** entry in `client_keys.json` for the work generator.
- `env_files/dashboard.env` for Redis hostname and logging.

Details and optional variables: **[env_files.md](env_files.md)**.

Client behavior, logging, persistence outcomes (JSON, tombstones, unparseable bodies), and scaling guidance: **[client.md](client.md)**, **[client_logging.md](client_logging.md)**, and **[structure.md](structure.md)**.

## Build and run

Build images:

```bash
docker compose build
```

Start all services in the background:

```bash
docker compose up -d
```

Omit `-d` to run attached to the terminal; use **Ctrl+C** to stop.

Stop and remove containers:

```bash
docker compose down
```

Recent logs for the download client:

```bash
docker compose logs --tail=25 client
```

Omit `--tail=25` only if you need the full history.

## Helper scripts

`devup` (optional `-b` to build first) and `devdown` in the repository root call Docker Compose to start or stop the full stack defined in `docker-compose.yml`.
