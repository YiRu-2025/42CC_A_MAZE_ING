*This activity has been created as part of the 42 curriculum by sluyu, yru.*

# A-Maze-ing

## Description

A-Maze-ing reads a configuration file, generates a maze, solves it, writes it
to a file with a hexadecimal wall encoding, and displays it in the terminal
with a small interactive menu.

Two kinds of maze can be requested with the `PERFECT` key:

- **`PERFECT=True`**: a *perfect* maze. It is a spanning tree of the grid:
  every cell can be reached and there is exactly one path between any two
  cells, so no loop anywhere.
- **`PERFECT=False`**: a board usable by a Pac-Man-like game. It is fully
  connected, offers many independent routes (loops), has almost no
  dead-end, and keeps the four corners and the centre open.

In both modes:

- a visible **"42"** is drawn in the middle with fully closed cells (it needs
  a maze of at least 7x5 cells);
- the outer border is closed;
- no corridor is wider than two cells (no fully open 3x3 area);
- the same `SEED` always gives the same maze.

The generation lives in a standalone package, `mazegen`, built as a wheel
(`mazegen-1.0.0-py3-none-any.whl`, at the root of this repository) so a later
project can install and reuse it.

### Features

- Configuration parsing with precise error messages (line numbers).
- Perfect and playable generation, reproducible with a seed.
- Shortest path with a breadth-first search.
- Output file following the subject's format.
- Terminal display with the path, wall colours and "42" colours.
- Independent validation of every generated maze.
- Unit tests, `flake8` and `mypy` clean (also with `--strict`).

## Instructions

Requirements: Python 3.10 or later. The program itself only uses the standard
library; the development tools are listed in `requirement.txt`
(`flake8`, `mypy`, `build`, `pytest`).

```bash
make install     # create the virtual environment amaze-virtual and install the tools
make run         # python3 a_maze_ing.py config.txt
make debug       # run under pdb
make test        # unit tests (pytest)
make lint        # flake8 + mypy
make lint-strict # flake8 + mypy --strict
make build       # build the package and copy the wheel to the repository root
make clean       # remove caches and build artifacts
make fclean      # clean + remove the virtual environment and maze.txt
make re          # fclean, install, build
```

Without `make`:

```bash
python3 a_maze_ing.py config.txt
```

### Interactive menu

After the maze is written, it is drawn in the terminal and a menu is shown:

| Choice | Action |
|--------|--------|
| 1 | Re-generate a new maze (a fresh random one: `SEED` only applies to the first maze of a run) |
| 2 | Show or hide the shortest path |
| 3 | Rotate the colours of the walls |
| 4 | Rotate the colours of the "42" pattern |
| 5 | Quit |

The entry is drawn `S`, the exit `E`, and the "42" cells are coloured.

### Errors and warnings

Any error (missing file, invalid configuration, impossible parameters, file
that cannot be written) prints one clear line on the error output, starting
with `Error:`, and the program exits with code `1`. `Ctrl+C` or `Ctrl+D`
exits with `130`. The program never shows a Python traceback.

Some situations are not errors but are reported as a `Warning:` line:

- the maze is too small for the "42" (less than 7x5): it is omitted;
- the "42" would cut the maze into several parts: it is omitted;
- the playable board misses one of its criteria (never observed on
  mazes larger than 8x8, see "Algorithm").

An `ENTRY` or `EXIT` placed on a cell of the "42" is an error.

### Checking a result

```bash
python3 maze_analyzer.py maze.txt                    # analysis script of the subject
python3 maze_analyzer.py maze.txt --max-dead-ends 0  # also check the no-dead-end bonus
```

## Configuration file

One `KEY=VALUE` pair per line. Empty lines and lines starting with `#` are
ignored. Keys are case-insensitive and spaces around `=` are allowed.

| Key | Required | Meaning | Example |
|-----|----------|---------|---------|
| `WIDTH` | yes | Number of cells horizontally | `WIDTH=20` |
| `HEIGHT` | yes | Number of cells vertically | `HEIGHT=15` |
| `ENTRY` | yes | Entry cell, `x,y` | `ENTRY=0,0` |
| `EXIT` | yes | Exit cell, `x,y` | `EXIT=19,14` |
| `OUTPUT_FILE` | yes | File the maze is written to | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | yes | `True` or `False` | `PERFECT=False` |
| `SEED` | no | Integer, for a reproducible maze | `SEED=42` |

Rules enforced by the parser:

- `WIDTH` and `HEIGHT` are integers between 2 and 1000;
- `ENTRY` and `EXIT` are two integers `x,y` inside the maze, and different;
- `PERFECT` is `True` or `False` (any case);
- `OUTPUT_FILE` is not empty;
- every required key is present; an unknown or duplicated key is an error.

Coordinates start at `0,0` in the top-left corner; `x` goes right and `y`
goes down.

The default configuration is `config.txt`, at the root of the repository:

```
# WIDTH Maze width (number of cells)
WIDTH=20
# HEIGHT Maze height
HEIGHT=15
# ENTRY Entry coordinates (x,y)
ENTRY=0,0
# EXIT Exit coordinates (x,y)
EXIT=19,14
# OUTPUT_FILE Output filename
OUTPUT_FILE=maze.txt
# PERFECT Is the maze perfect?
PERFECT=True
# SEED Random seed for reproducible generation
SEED=42
```

## Output file

One hexadecimal digit per cell, row by row, one row per line. A bit set to 1
means the wall is **closed**: bit 0 north, bit 1 east, bit 2 south, bit 3 west
(so `1` = N, `2` = E, `4` = S, `8` = W, and `F` is a fully closed cell, like
the cells of the "42").

After an empty line come three lines: the entry coordinates, the exit
coordinates, and the shortest path written with the letters `N`, `E`, `S`, `W`.
Every line ends with `\n`. Two neighbouring cells always agree on the wall they
share.

```
D539553955553D517913
97C693C69553C53C56AA
8153AC55695697A9556A
AAD2C39396B943C6957A
...

0,0
19,14
EESENEEESENEEEEESEESSENEEENNESSSSWWWSWNWSSSENESSSWSESSESSENNNESSS
```

## Algorithm

### Generation: recursive backtracker

The maze is carved with the **recursive backtracker** (randomized
depth-first search), written with an **explicit stack** instead of recursion,
so a 1000x1000 maze cannot exceed the recursion limit of Python:

1. Draw the "42": its cells are marked as blocked and keep their four walls.
2. Start from the entry. While the stack is not empty, look at the cell on top:
   pick a random neighbour that is inside the maze, not blocked and not yet
   visited, open the wall between the two cells and push the neighbour. If
   there is none, pop the stack.
3. Every free cell is visited exactly once and every visit opens exactly one
   wall, so the result is a **spanning tree**: connected and loop-free. That
   is the definition of a perfect maze.

### Playable board (`PERFECT=False`)

The spanning tree is then reworked:

1. All internal walls between free cells are listed and shuffled.
2. Each wall is opened, unless this makes a completely open 3x3 area. Only the
   six 3x3 areas that contain both cells of the wall can change, so only those
   are tested.
3. The result is checked: at least two independent loops, at most two
   dead-ends that could still be opened, and open corners and centre. When a
   criterion is missed, step 1 to 2 are drawn again from the same tree (up to
   10 times, 2 for mazes larger than 10 000 cells). If it still fails, a
   warning is returned. On the 1 050 mazes tested (7 sizes from 8x8 to 60x60,
   150 seeds each) the first draw was always enough.

### Shortest path: breadth-first search

A breadth-first search from the entry reaches every cell by its shortest
route first, and the path is rebuilt from the exit with a table of
predecessors.

### Complexity

Generation, validation and solving are linear in the number of cells. On the
development machine a 1000x1000 maze takes about 4.5 s (perfect) and about
21 s (playable) to generate.

### Why this algorithm

| Algorithm | Result | Decision |
|-----------|--------|----------|
| Recursive backtracker | Long winding corridors, few branches | **Chosen**: simple, linear time, easy to make iterative, and the most maze-looking result |
| Prim's | Many short branches, uniform look | Needs a frontier set; the look is less twisty |
| Kruskal's | Elegant, uniform spanning tree | Needs a union-find structure for the same guarantee |

All three build a spanning tree, so all three satisfy `PERFECT=True`. The
choice was made on implementation cost, on the look of the maze, and because
long corridors leave room for many loops once walls are opened for the
playable mode. Opening the walls in random order while forbidding open 3x3
areas is a simple greedy method that removes the dead-ends without any
special case.

## Reusable part

Everything under `mazegen/` is independent from the program: it never reads a
file, never prints, and does not know that a configuration file exists. The
files `a_maze_ing.py`, `config_parser.py`, `exporter.py` and `visualizer.py`
belong to this program only.

Build and install:

```bash
make build                                  # or: python3 -m build
pip install mazegen-1.0.0-py3-none-any.whl
```

Instantiate and use the generator, pass parameters, read the structure and a
solution:

```python
from mazegen import MazeGenerator, check_all, path_to_letters

maze = MazeGenerator(
    width=20, height=15,            # size, in cells
    entry=(0, 0), exit_cell=(19, 14),
    perfect=True,                   # False: playable board
    seed=42,                        # reproducible
)
grid = maze.generate()              # same object as maze.grid

check_all(maze.grid, maze.blocked, perfect=True)  # raises MazeError if invalid
path = maze.solve()                 # [(0, 0), (1, 0), ...]
print(path_to_letters(path))        # "EESENEEESEN..."
```

| Need | How |
|------|-----|
| Custom parameters | `width`, `height`, `entry`, `exit_cell`, `perfect`, `seed`, and `openness` (0 to 1, share of the extra passages opened in playable mode) |
| The maze | `maze.grid[y][x]`: an integer per cell, a bit set to 1 is a closed wall (`NORTH=1`, `EAST=2`, `SOUTH=4`, `WEST=8`) |
| The "42" cells | `maze.blocked`: set of `(x, y)`; `maze.pattern_placed` tells if it is drawn |
| A solution | `maze.solve()`, or `solve(grid, entry, exit)`; `NoPathError` if none |
| What went wrong softly | `maze.warnings`: list of strings (pattern omitted, criteria missed) |
| Invalid parameters | `ValueError` |

The full documentation is in `mazegen/README.md`, which is also the
description embedded in the package.

## Project structure

```
a_maze_ing.py        main program: config -> generate -> check -> solve -> write -> menu
config_parser.py     reads and validates the configuration file
exporter.py          writes the output file
visualizer.py        terminal drawing, colours and menu
maze_analyzer.py     analysis script provided with the subject
mazegen/             reusable package
  constants.py       direction bits, offsets, opposite directions, letters
  grid.py            shared helper: open neighbours of a cell
  generator.py       MazeGenerator: "42", spanning tree, playable board
  solver.py          breadth-first search and path as letters
  validator.py       coherence, border, 3x3, connectivity, loops, dead-ends
  README.md          documentation of the package
tests/test_maze.py   unit tests
config.txt           default configuration
Makefile, pyproject.toml, requirement.txt, .flake8, .gitignore
mazegen-1.0.0-py3-none-any.whl   built package
LICENSE.md
```

`grid[y][x]` stores the four walls of a cell in four bits. Every wall change
goes through two functions that edit both neighbouring cells at once, so the
shared walls cannot disagree.

## Team and project management

### Roles

| Member | Role |
|--------|------|
| sluyu | Configuration parsing and validation (`config_parser.py`), shortest-path solver (`mazegen/solver.py`), output writer (`exporter.py`), validation helpers (`mazegen/validator.py`) |
| yru | Generation algorithms (`mazegen/generator.py`), the "42" pattern, the playable-board mode, terminal display (`visualizer.py`) |

The split follows the border of the reusable module: one member owned the
generation itself, the other owned everything that reads from or writes to the
outside world (configuration, output file, terminal), plus the solver and the
validation helpers, which only read a maze and never modify it.

### Planning and how it evolved

1. **Agree on the interfaces first**: the wall bit encoding, `(x, y)`
   coordinates, and the `grid[y][x]` layout, so both members could work in
   parallel.
2. **Core part**: parser, generator, solver, exporter and validator. The first
   commit closed this stage, with the display still to do.
3. **Visual part**: the terminal drawing and the interactive menu.
4. **Checks and review**: unit tests, the analysis script, and `flake8` /
   `mypy`. The second commit closed this stage and left a review to do.
5. **Review and polish**: the code was compared with the subject. This brought
   the explicit playable-board criteria with retries, the fallback when the
   "42" does not fit, stricter configuration parsing (unknown keys), a faster
   3x3 test, the build of the package at the root, and this README brought back
   in line with the code.

The plan stayed the same; what changed is that the playable mode, which first
relied on the greedy opening alone, got explicit checks once the review showed
nothing guaranteed its criteria.

### What worked well, what could be improved

Worked well:

- agreeing on the data format before writing code, and splitting along the
  border of the reusable module;
- checking every maze with an independent validator and with the analysis
  script of the subject, over many sizes and seeds;
- seeds, which made every bug reproducible.

To improve:

- the README drifted from the code during development; documentation should be
  updated in the same commit as the code;
- tests should have been written together with the first version, not at the
  end;
- a playable maze of 1000x1000 takes about 21 s; the 3x3 test could be made
  cheaper still;
- the optional graphical rendering and extra generation algorithms are not
  implemented; the generator could take the algorithm as a parameter.

### Tools

- **Git and GitHub** for versioning.
- **Make** and a **virtual environment** (`venv`) for a reproducible setup.
- **flake8** (style), **mypy** (types, also with `--strict`), **pytest**
  (tests).
- **build** and **setuptools** to produce the wheel.
- **`maze_analyzer.py`** (provided) as an independent judge of the result.
- **`pdb`** (`make debug`) for step-by-step debugging.
- An **AI assistant**, see below.

## Resources

- Jamis Buck, *Mazes for Programmers: Code Your Own Twisty Little Passages*,
  the reference book on maze algorithms.
- Jamis Buck's blog series on maze algorithms, with animated demos.
- Wikipedia: "Maze generation algorithm", "Spanning tree", "Breadth-first
  search", "Depth-first search".
- Python documentation: `random.Random`, `collections.deque`, `typing`,
  `argparse`, `shutil.get_terminal_size`.
- Python Packaging User Guide: `pyproject.toml` and `build`.
- The documentation of `flake8`, `mypy` and `pytest`.

### Use of AI

An AI assistant (Claude) was used for:

- **understanding the subject**: the hexadecimal wall encoding, why the
  recursive backtracker must use an explicit stack, why a breadth-first search
  gives the shortest path, how to split the reusable module from the program;
- **reviewing the code against the subject**: finding the gaps between the
  README and the code, the missing deliverables (wheel at the root,
  `.gitignore`) and the lint issues;
- **proposing optimisations and tests**: the explicit playable criteria, the
  smaller set of 3x3 areas to test, the stricter configuration parser, the unit
  tests;
- **drafting documentation**: this README and `mazegen/README.md`.

The team reviewed, ran and tested every proposed change (unit tests,
`flake8`, `mypy`, the analysis script on many sizes and seeds) and is
responsible for the code. Parts of the generation, the parser and the solver
were written by the team before any AI review.

## License

MIT, see `LICENSE.md`. It was chosen because the subject requires the
generator to be reusable and redistributable by a later project: the MIT
license allows reuse, modification and distribution with almost no condition,
whereas a copyleft license such as the GPL would force every project building
on this one to adopt the same license.
