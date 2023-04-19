FROM python:3.8-slim-buster

WORKDIR /app

RUN python3 -m venv .venv

COPY mirrulations-client . 
COPY mirrulations-core /mirrulations-core
COPY mirrulations-client /mirrulations-client

RUN .venv/bin/pip install -e .
RUN .venv/bin/pip install /mirrulations-core
RUN .venv/bin/pip install /mirrulations-client

CMD [".venv/bin/python", "src/mirrclient/client.py"]