## Production Environment Documentation

The system is Dockerized into a number of components:

* `nginx` - A reverse proxy that routes requests to the dashboard
* `redis` - Job management as well as permanent variable storage
* `work_generator` - Finds new data and generates jobs to download from regulations.gov
* `rabbitmq` - Job Queue Management
* `dashboard` - Web-based user interface to observe progress and system status
* `client` - Downloads data from regulations.gov (uses `env_files/client_keys.json`)

## Docker Compose commands

* `docker compose build` to build containers
* `docker compose up -d` to start all containers (`-d` to run in background)
* `docker compose logs` to see logs.  
	* `--tail=<number>` add to display a specific number of logs
	* add a container name to see individual container logs
* `docker compose down` to bring the system down
* `docker compose stop <name>` to stop a particular container
* `docker compose ps` list all of the docker containers and their states

See [docker compose documentation] (https://docs.docker.com/compose/reference/) for more information:
