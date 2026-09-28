.PHONY: install run debug clean lint lint-strict

VENV = amaze-virtual
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# install
install:
	python3 -m venv $(VENV) 
	$(PIP) install -r requirements.txt

# run
run:
	$(PYTHON) a_maze_ing.py config.txt

# debug
debug:
	$(PYTHON) -m pdb a_maze_ing.py config.txt

# clean
clean:
	rm -rf __pycache__ .mypy_cache

# lint
lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# lint-strict
lint-strict:
	flake8 .
	mypy . --strict

build:
	python3 -m build
	cp dist/mazegen-*.whl .
