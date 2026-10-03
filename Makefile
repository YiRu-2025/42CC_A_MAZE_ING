.PHONY: install run debug clean fclean lint lint-strict re build


# install
install:
	pip install -r requirement.txt

# run
run:
	python3 a_maze_ing.py config.txt

# debug
debug:
	python3 -m pdb a_maze_ing.py config.txt

# clean and fclean
clean:
	rm -rf __pycache__ mazegen/__pycache__ tests/__pycache__
	rm -rf .mypy_cache .pytest_cache

fclean: clean
	rm -rf build dist *.egg-info
	rm -f maze.txt

re: fclean
	python3 -m build

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
