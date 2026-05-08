FROM python:3

WORKDIR /app
RUN apt-get update; apt-get install docker.io -y
RUN python3 -m venv .venv

COPY mirrulations-dashboard .
COPY mirrulations-core /mirrulations-core

RUN .venv/bin/pip install -e .
RUN .venv/bin/pip install /mirrulations-core

CMD [".venv/bin/gunicorn", "--bind", "0.0.0.0:5000", "--timeout", "120", "-m", "007", "mirrdash.wsgi:app"]
