"""Small helpers shared by the solver and the validator."""

from collections.abc import Iterator

from .constants import ALL_DIRECTIONS, DELTA

Cell = tuple[int, int]
Grid = list[list[int]]


def open_neighbours(grid: Grid, cell: Cell) -> Iterator[Cell]:
    """Yield the neighbours reachable from a cell without crossing a wall."""
    x, y = cell
    height = len(grid)
    width = len(grid[0])
    walls = grid[y][x]

    for direction in ALL_DIRECTIONS:
        if walls & direction:
            continue
        next_x = x + DELTA[direction][0]
        next_y = y + DELTA[direction][1]
        if 0 <= next_x < width and 0 <= next_y < height:
            yield next_x, next_y
