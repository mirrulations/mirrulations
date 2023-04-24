# NOTE: This file MUST use tabs for indentation rather than spaces
#       If you get an error "*** missing separator. Stop" then you
#       probably have spaces for indentation.
export PATH:=${PWD}/.venv/bin:${PATH};

all: test static

test:
	pytest;

static:
	flake8 mirrulations-client mirrulations-dashboard mirrulations-work-generator mirrulations-extractor mirrulations-mocks mirrulations-validation mirrulations-core;
	pycodestyle mirrulations-client mirrulations-dashboard mirrulations-work-generator mirrulations-extractor mirrulations-mocks mirrulations-validation mirrulations-core;
	pylint mirrulations-client mirrulations-dashboard mirrulations-work-generator mirrulations-extractor mirrulations-mocks mirrulations-validation mirrulations-core;


clean:
	# Find and remove all files and  folders that match
    # -E for extended grep to match the pattern
	-find . | grep -E "(__pycache__|\.pyc)" | xargs rm -rf
    # -w for whole word so it does not match .coveragerc
	-find . | grep -w "unit-python.xml" | xargs rm -rf
	-find . | grep -w ".coverage" | xargs rm -rf
	-find . | grep -w "htmlcov" | xargs rm -rf
	-find . | grep -w ".pytest_cache" | xargs rm -rf
	-find . | grep -w ".vagrant" | xargs rm -rf
