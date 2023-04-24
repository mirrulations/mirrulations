#!/bin/sh

if [ ! -d "./.venv" ] 
then
    python3 -m venv .venv

fi

.venv/bin/pip install -e mirrulations-client
.venv/bin/pip install -e mirrulations-core
.venv/bin/pip install -e mirrulations-dashboard
.venv/bin/pip install -e mirrulations-mocks
.venv/bin/pip install -e mirrulations-work-generator 
.venv/bin/pip install -e mirrulations-extractor 
.venv/bin/pip install -e mirrulations-validation