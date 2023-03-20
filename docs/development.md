
## Developer Setup

* Create and activate a virtual environment

  ```
  python3 -m venv .venv
  source .venv/bin/activate
  ```

* Install source code as a module

  The project is organized into multiple modules, which must each be installed as "editable"
  (using the `-e` switch on `pip`):

  ```
  pip install -e mirrulations-client
  pip install -e mirrulations-core
  pip install -e mirrulations-dashboard
  pip install -e mirrulations-mocks
  pip install -e mirrulations-work-generator 
  pip install -e mirrulations-work-server
  pip install -e mirrulations-extractor
  ```

## Run Static Analysis and Tests

Type `make` to run all. 

Type `make static` for only static tests.

Type `make test` for only pytest.  Alternatively, run `pytest` in the root of
the project to run all tests.  You can run `pytest` in any of module folders
(e.g. in `mirrulations-client`) to run tests for just that module.  Note that
there are `pytest.ini` files in each module as well as a global `pytest.ini`.

* Static analysis uses `flake8`, `pycodestyle`, and `pylint`
* `pytest` uses a coverage metric of 95%.
* NOTE: Sometimes if `pytest` is installed globally, the virtual environment will use that instead. Simply exit and reenter the virtual environment to resolve this.
  Alternatively, uninstall `pytest` from the global packages (`pip3 uninstall pytest` in new terminal).


## Setup for Local Launch

The system is made up of a number of Docker containers.  See the `docker-compose.yml` file for details.

* **Work Generator** - Uses an API key to query regulations.gov in order to determine what data needs to be downloaded
* **Work Server** - Provides jobs to clients and saves results returned by clients
* **Redis** - Database used to maintain work queues
* **Mongo** - Database used to hold results
* **Dashboard** - Provides a status page for the system
* **NGINX** - Routes web traffic to appropriate host (currently only the dashboard)
* **Clients** - There are multiple instances of the clients.  Each gets jobs from the work server, downloads the requested information from regulations.gov (using an API key), and returns the data to the work server.
* **Extractor** - Walks through the data and extracts text from attachments. The text is then saved to the appropriate location.

### Docker Setup

To run the system locally, you have to specify the API key for each client and for the work generator.  It is important that you **DO NOT** use any of the API keys used in production.

Because a local instance of the system should only run for a short period of time, we use a single API key for the work generator and all the clients:

To get an api key, visit [here](https://open.gsa.gov/api/regulationsgov/). 

To make all neccessary files for the clients, dashboard, and the work generator, run `python dev_setup.py`.

## Launch Locally

* Build the Docker containers

  ```
  docker-compose build
  ```
  
* Launch all the containers

  ```
  docker-compose up -d
  ```
  
  If you forget the `-d`, it will launch in the foreground, and you will see the log output for all containers. Press ctlr-c to exit all containers

* Using devup to Build and Launch Docker Containers

  ```
  bash devup [-b]
  ```

  Running devup will launch the docker containers for you. Along with the optional `-b` you can build and launch the containers simaltaniously. 
  
* Kill all containers

  ```
  docker-compose down
  ```

  or you could do

  ```
  bash devdown
  ```
  
* To see the last 25 log messages of one container (`client1` in this example):

  ```
  docker-compose logs --tail=25 client1
  ```
  
  If you forget `--tail=25`, it will show **all** log messages.
