FROM python:3

WORKDIR /app

RUN python3 -m venv .venv

COPY mirrulations-work-generator .
COPY mirrulations-core /mirrulations-core

RUN .venv/bin/pip install -e .
RUN .venv/bin/pip install -e /mirrulations-core/

CMD [".venv/bin/python", "src/mirrgen/work_generator.py"]
