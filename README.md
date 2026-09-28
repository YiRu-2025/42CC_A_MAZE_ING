*This activity has been created as part of the 42 curriculum by sluyu, yru.*

# A-Maze-ing

## Description

A-Maze-ing generates a maze from a configuration file, solves it, writes
it to a file using a hexadecimal wall encoding, and displays it in the
terminal with a small interactive menu.

Two generation modes are available:

- **`PERFECT=True`** — a perfect maze: exactly one path links the entry
  and the exit, and there is no loop anywhere.
- **`PERFECT=False`** (default) — a board usable by a Pac-Man-like game:
  fully connected, several independent routes, open corners and centre,
  and almost no dead-end.

In both modes the maze contains a visible "42" drawn with fully closed
cells, and no corridor is wider than two cells.

The generation itself lives in a standalone package, `mazegen`, which is
built as a wheel so a later project can install and reuse it.

## Instructions

```bash
make install     # install the development dependencies
make run         # python3 a_maze_ing.py config.txt
make lint        # flake8 and mypy
make clean       # remove caches and build artifacts
```

Running the program directly:

```bash
python3 a_maze_ing.py config.txt
```

While the program runs, the menu offers:

1. re-generate a new maze;
2. show or hide the shortest path;
3. rotate the colors of the walls;
4. quit.

Any error — missing file, invalid configuration, impossible parameters —
prints a single clear message and exits with the code 1.

## Configuration file

One `KEY=VALUE` pair per line. Empty lines and lines starting with `#`
are ignored. Keys are case-insensitive.

| Key | Required | Meaning | Example |
|-----|----------|---------|---------|
| `WIDTH` | yes | Number of cells horizontally | `WIDTH=20` |
| `HEIGHT` | yes | Number of cells vertically | `HEIGHT=15` |
| `ENTRY` | yes | Entry coordinates, `x,y` | `ENTRY=0,0` |
| `EXIT` | yes | Exit coordinates, `x,y` | `EXIT=19,14` |
| `OUTPUT_FILE` | yes | File the maze is written to | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | yes | `True` or `False` | `PERFECT=False` |
| `SEED` | no | Integer, for reproducible mazes | `SEED=42` |

Rules enforced by the parser: `WIDTH` and `HEIGHT` are integers between
5 and 1000, the entry and the exit are inside the maze and are different
cells, `OUTPUT_FILE` is not empty, and an unknown or duplicated key is
an error.

The default configuration is `config.txt`, at the root of the
repository.

## Output file

The maze is written with one hexadecimal digit per cell. A bit set to 1
means the wall is closed: bit 0 is north, bit 1 is east, bit 2 is south,
bit 3 is west. Cells are stored row by row, one row per line.

After an empty line come three lines: the entry coordinates, the exit
coordinates, and the shortest path written with the letters `N`, `E`,
`S` and `W`. Every line ends with `\n`.

```
91395539555539513913
86C693C69553C43C46AA
...

0,0
19,14
SSSSSESWSSEEEEESENESSSSEEENNEEESEESSEESEE
```

The file can be checked with the analysis script provided with the
subject:

```bash
python3 maze_analyzer.py maze.txt
```

## Algorithm

The maze is carved with the **recursive backtracker**, written with an
explicit stack rather than recursion so a large maze cannot exceed the
recursion limit of Python. It produces a spanning tree of the grid,
which is exactly the definition of a perfect maze.

When `PERFECT=False`, the perfect maze is then reworked: dead-ends are
opened (*braiding*), the corners and the centre are forced to be open
corridors, and extra walls are opened until the board offers at least
two independent routes. Every wall removal is refused when it would
create a completely open 3x3 area.

The shortest path is found with a **breadth-first search**, which
reaches every cell by its shortest route first.

### Why this algorithm

| Algorithm | Result | Why not chosen |
|-----------|--------|----------------|
| Recursive backtracker | Long winding corridors, few branches | **Chosen**: simplest to implement, linear time, and the most maze-looking result |
| Prim's | Short, evenly spread branches | Needs a frontier set, and the result looks more uniform than we wanted |
| Kruskal's | Mathematically elegant | Needs a union-find structure for a result of the same quality |

All three produce a spanning tree, so all three satisfy `PERFECT=True`.
The choice was made on implementation cost and on the look of the maze.


## Reusable part

Everything under `mazegen/` is independent from this program: it never
reads a file, never prints anything, and does not know that a
configuration file exists. It is built as `mazegen-1.0.0-py3-none-any.whl`,
at the root of the repository.

```python
from mazegen import MazeGenerator, check_all
from mazegen.solver import solve, path_to_letters

maze = MazeGenerator(width=20, height=15, entry=(0, 0), exit_cell=(19, 14),
                     perfect=True, seed=42)
maze.generate()
check_all(maze.grid, maze.blocked)
print(path_to_letters(solve(maze.grid, maze.entry, maze.exit)))
```

`maze.grid` holds one integer per cell, with the same bit encoding as
the output file. The full documentation is in `mazegen/README.md`.

Rebuilding the package from the sources:

```bash
python3 -m venv venv && source venv/bin/activate
pip install build
python3 -m build
```

The repository files that are not part of the reusable module —
`a_maze_ing.py`, `config_parser.py`, `exporter.py`, `visualizer.py` —
belong to this program only.

## Team and project management

| Member | Role |
|--------|------|
| sluyu | Configuration parsing and validation (`config_parser.py`), shortest-path solver (`mazegen/solver.py`), output file writer (`exporter.py`), maze validation helpers (`mazegen/validator.py`)|
| yru | Maze generation algorithms (`mazegen/generator.py`), the '42' pattern, the playable-board mode, terminal display (`visualizer.py`) |

The split follows the border of the reusable module: one of us owned the
generation itself, the other owned everything that reads from or writes
to the outside world — configuration, output file, terminal — plus the
solver and the validation helpers, which only read a maze and never
modify it.

## Resources

- Jamis Buck, *Mazes for Programmers: Code Your Own Twisty Little
  Passages* — the reference book on maze generation algorithms.
- Jamis Buck's blog series on maze algorithms, with animated demos.
- Wikipedia, "Maze generation algorithm" and "Spanning tree".
- Python documentation: `random.Random`, `collections.deque`,
  `typing`, `setuptools` packaging guide.

### Use of AI

AI was used to explain the subject, to review our code, and to discuss
design choices:
the bit encoding of the walls, why the recursive backtracker had to be written
with an explicit stack, why a breadth-first search is required for the
shortest path, and how to split the reusable module from the program.
Every piece of code in this repository was written, tested and is
understood by the team; the validation functions and the analysis
script were used to check the results independently.

## License

MIT. See `LICENSE.md`. This license was chosen because the subject
requires the generator to be reusable and redistributable by a later
project: MIT allows reuse, modification and distribution with almost no
condition, where a copyleft license such as the GPL would force every
project building on this one to adopt the same license.
