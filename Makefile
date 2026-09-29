.PHONY: install run debug clean fclean lint lint-strict

VENV = amaze-virtual
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# install
install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirement.txt

# run
run:
	$(PYTHON) a_maze_ing.py config.txt

# debug
debug:
	$(PYTHON) -m pdb a_maze_ing.py config.txt

# clean and fclean
clean:
	rm -rf __pycache__ mazegen/__pycache__ tests/__pycache__
	rm -rf .mypy_cache .pytest_cache
	rm -rf amaze-virtual

fclean: clean
	rm -rf build dist *.egg-info
	rm -f maze.txt
	rm -f mazegen-1.0.0*

re: fclean
	python3 -m build
	cp dist/mazegen-*.whl .

# lint
lint:
	flake8 .
	mypy . --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs

# lint-strict
lint-strict:
	flake8 .
	mypy . --strict

build:
	pip install build
	python3 -m build
	cp dist/mazegen-*.whl .
