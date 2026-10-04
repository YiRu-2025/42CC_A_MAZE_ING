.PHONY: install run debug test clean fclean re build lint lint-strict

VENV = amaze-virtual
PYTHON = $(VENV)/bin/python
PIP = $(VENV)/bin/pip

# install the development tools in a virtual environment
install:
	python3 -m venv $(VENV)
	$(PIP) install -r requirement.txt

# run the program with the default configuration
run:
	$(PYTHON) a_maze_ing.py config.txt

# run the program under the Python debugger
debug:
	$(PYTHON) -m pdb a_maze_ing.py config.txt

# run the unit tests
test:
	$(PYTHON) -m pytest -q

# remove caches and build artifacts
clean:
	rm -rf __pycache__ mazegen/__pycache__ tests/__pycache__
	rm -rf .mypy_cache .pytest_cache
	rm -rf build dist *.egg-info

# also remove the virtual environment and the generated maze
# (the mazegen-*.whl at the root is a deliverable and is kept)
fclean: clean
	rm -rf $(VENV)
	rm -f maze.txt

# rebuild everything from scratch
re: fclean install build

# build the reusable package and copy it to the root of the repository
build:
	$(PYTHON) -m build
	rm -f mazegen-*.whl
	cp dist/mazegen-*.whl .

lint:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	$(PYTHON) -m flake8 .
	$(PYTHON) -m mypy . --strict
