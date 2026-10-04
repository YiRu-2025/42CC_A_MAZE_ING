# mazegen

A small, dependency-free maze generator. It builds either a **perfect
maze** (one path between two cells, no loop) or a **board playable by a
Pac-Man-like game** (fully connected, several routes, almost no
dead-end). A "42" made of fully closed cells is drawn in the middle
whenever the maze is large enough (at least 7x5).

The package never reads a file and never prints.

## Install

```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

## Basic example

```python
from mazegen import MazeGenerator, check_all, path_to_letters, solve

maze = MazeGenerator(width=20, height=15, entry=(0, 0),
                     exit_cell=(19, 14), perfect=True, seed=42)
maze.generate()

check_all(maze.grid, maze.blocked, perfect=True)   # raises MazeError
path = maze.solve()                                # list of (x, y) cells
print(path_to_letters(path))                       # "SSEE..."
```

## Parameters

| Parameter | Meaning |
|-----------|---------|
| `width`, `height` | Size in cells, at least 2 |
| `entry`, `exit_cell` | `(x, y)` cells, inside the maze and different |
| `perfect` | `True`: no loop. `False` (default): playable board |
| `seed` | Integer for a reproducible maze (`None`: random) |
| `openness` | 0 to 1, share of the legal extra passages opened when `perfect=False` (default 1) |

`ValueError` is raised for an invalid parameter, or when the entry or
the exit falls inside the "42" pattern.

## Reading the result

- `maze.grid[y][x]`: one integer per cell. A bit set to 1 is a closed
  wall: `1` north, `2` east, `4` south, `8` west (constants `NORTH`,
  `EAST`, `SOUTH`, `WEST`). Two neighbours always agree on their shared
  wall.
- `maze.blocked`: set of `(x, y)` cells that draw the "42".
- `maze.solve()`: shortest path from entry to exit, both included.
  `solve(grid, entry, exit)` does the same for any grid.
  `NoPathError` is raised if there is none.
- `maze.warnings`: list of strings describing what could not be done as
  requested (pattern omitted because the maze is too small or would
  disconnect it, playable criteria not fully met). `maze.pattern_placed`
  tells whether the "42" is there.
- `check_all(grid, blocked, perfect=False)`: checks wall coherence, closed
  border, no 3x3 open area and connectivity (and the absence of loops
  when `perfect=True`). Raises `MazeError`.

## Algorithm

Recursive backtracker (randomized depth-first search) with an explicit
stack, giving a spanning tree. For `perfect=False`, extra walls are then
opened in random order, each one only if no 3x3 area becomes open. The
shortest path is found with a breadth-first search.

## License

MIT.
