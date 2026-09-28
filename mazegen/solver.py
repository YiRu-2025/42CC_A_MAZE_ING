"""Find the shortest path between two cells of a maze"""

from collections import deque
from .constants import ALL_DIRECTIONS, DELTA, LETTER


class NoPathError(Exception):
    """Raised when no path exists between the entry and the exit."""


def _open_neighbours(
    grid: list[list[int]], cell: tuple[int, int]
) -> list[tuple[int, int]]:
    """List the neighbours that can be reached without crossing a wall.
    Returns:
    The coordinates of every neighbour reachable in one step.
    """
    x, y = cell
    height = len(grid)
    width = len(grid[0])
    neighbours = []

    for direction in ALL_DIRECTIONS:
        if grid[y][x] & direction:
            continue
        next_x = x + DELTA[direction][0]
        next_y = y + DELTA[direction][1]
        if 0 <= next_x < width and 0 <= next_y < height:
            neighbours.append((next_x, next_y))
    return neighbours


def _rebuild_path(
    came_from: dict[tuple[int, int], tuple[int, int]],
    entry: tuple[int, int],
    exit_cell: tuple[int, int],
) -> list[tuple[int, int]]:
    """Walk back from the exit to the entry and reverse the result.

    Returns:
        The list of cells from the entry to the exit, both included.
    """
    path = [exit_cell]
    cell = exit_cell
    while cell != entry:
        cell = came_from[cell]
        path.append(cell)
    path.reverse()
    return path


def solve(
    grid: list[list[int]], entry: tuple[int, int], exit_cell: tuple[int, int]
) -> list[tuple[int, int]]:
    """Find the shortest path from the entry to the exit.
    Returns:
        The list of cells from the entry to the exit, both included.
    """
    if entry == exit_cell:
        return [entry]
    came_from: dict[tuple[int, int], tuple[int, int]] = {}
    seen = {entry}
    queue = deque([entry])

    while queue:
        cell = queue.popleft()
        if cell == exit_cell:
            return _rebuild_path(came_from, entry, exit_cell)
        for neighbour in _open_neighbours(grid, cell):
            if neighbour in seen:
                continue
            seen.add(neighbour)
            came_from[neighbour] = cell
            queue.append(neighbour)

    raise NoPathError(f"no path from {entry} to {exit_cell}")


def path_to_letters(path: list[tuple[int, int]]) -> str:
    """Turn a list of cells into the N/E/S/W string of the output file."""
    letters = []

    for (x1, y1), (x2, y2) in zip(path, path[1:]):
        step = (x2 - x1, y2 - y1)
        for direction in ALL_DIRECTIONS:
            if DELTA[direction] == step:
                letters.append(LETTER[direction])
                break
        else:
            raise ValueError(f"cells ({x1},{y1}) and ({x2},{y2}) are apart")
    return "".join(letters)
