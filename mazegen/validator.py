"""Check that a generated maze respects the rules of the subject.

Every function only reads the grid and never modifies it.
"""

from .constants import ALL_DIRECTIONS, DELTA, EAST, NORTH, SOUTH, WEST
from .grid import Cell, Grid, open_neighbours

# A cell with exactly one open side has three closed walls.
_THREE_WALLS = frozenset({
    NORTH | EAST | SOUTH,
    NORTH | EAST | WEST,
    NORTH | SOUTH | WEST,
    EAST | SOUTH | WEST,
})


class MazeError(Exception):
    """Raised when a generated maze breaks one of the subject's rules."""


def has_wall(grid: Grid, x: int, y: int, direction: int) -> bool:
    """Tell whether a cell has a wall on the given side."""
    return bool(grid[y][x] & direction)


def check_coherence(grid: Grid) -> None:
    """Check that two neighbours agree about the wall they share.

    Only the east and south sides are tested, because every shared wall
    is then looked at exactly once.
    """
    height = len(grid)
    width = len(grid[0])

    for y in range(height):
        for x in range(width):
            if x < width - 1:
                if has_wall(grid, x, y, EAST) != has_wall(
                    grid, x + 1, y, WEST
                ):
                    raise MazeError(
                        f"wall mismatch between ({x},{y}) east "
                        f"and ({x + 1},{y}) west"
                    )
            if y < height - 1:
                if has_wall(grid, x, y, SOUTH) != has_wall(
                    grid, x, y + 1, NORTH
                ):
                    raise MazeError(
                        f"wall mismatch between ({x},{y}) south "
                        f"and ({x},{y + 1}) north"
                    )


def check_border(grid: Grid) -> None:
    """Check that the outer border of the maze is fully closed."""
    height = len(grid)
    width = len(grid[0])

    for x in range(width):
        if not has_wall(grid, x, 0, NORTH):
            raise MazeError(f"cell ({x},0) is open to the north border")
        if not has_wall(grid, x, height - 1, SOUTH):
            raise MazeError(
                f"cell ({x},{height - 1}) is open to the south border"
            )
    for y in range(height):
        if not has_wall(grid, 0, y, WEST):
            raise MazeError(f"cell (0,{y}) is open to the west border")
        if not has_wall(grid, width - 1, y, EAST):
            raise MazeError(
                f"cell ({width - 1},{y}) is open to the east border"
            )


def _is_open_block(grid: Grid, left: int, top: int) -> bool:
    """Tell whether the 3x3 area with this top-left corner is fully open."""
    for y in range(top, top + 3):
        for x in range(left, left + 3):
            if x < left + 2 and has_wall(grid, x, y, EAST):
                return False
            if y < top + 2 and has_wall(grid, x, y, SOUTH):
                return False
    return True


def check_no_open3x3(grid: Grid) -> None:
    """Check that no 3x3 area of the maze is completely open."""
    height = len(grid)
    width = len(grid[0])
    for top in range(height - 2):
        for left in range(width - 2):
            if _is_open_block(grid, left, top):
                raise MazeError(f"3x3 open area starting at ({left},{top})")


def check_connectivity(grid: Grid, blocked: set[Cell]) -> None:
    """Check that every cell can be reached, except the '42' pattern.

    A flood fill is started from the first cell that is not part of the
    pattern, and the number of visited cells is compared with the number
    of cells that should be reachable.

    Args:
        grid: The wall grid.
        blocked: Coordinates of the cells forming the '42' pattern.
    """
    height = len(grid)
    width = len(grid[0])
    start = next(
        (
            (x, y)
            for y in range(height)
            for x in range(width)
            if (x, y) not in blocked
        ),
        None,
    )
    if start is None:
        raise MazeError("every cell belongs to the '42' pattern")

    seen = {start}
    stack = [start]
    while stack:
        for neighbour in open_neighbours(grid, stack.pop()):
            if neighbour not in seen:
                seen.add(neighbour)
                stack.append(neighbour)

    expected = width * height - len(blocked)
    if len(seen) != expected:
        raise MazeError(
            f"maze is not fully connected: {len(seen)} cells reachable "
            f"out of {expected}"
        )


def _count_passages(grid: Grid, blocked: set[Cell]) -> int:
    """Count the open passages between two cells that are not blocked."""
    height = len(grid)
    width = len(grid[0])
    passages = 0
    for y in range(height):
        for x in range(width):
            if (x, y) in blocked:
                continue
            if (
                x < width - 1
                and (x + 1, y) not in blocked
                and not has_wall(grid, x, y, EAST)
            ):
                passages += 1
            if (
                y < height - 1
                and (x, y + 1) not in blocked
                and not has_wall(grid, x, y, SOUTH)
            ):
                passages += 1
    return passages


def count_loops(grid: Grid, blocked: set[Cell]) -> int:
    """Count the independent loops of a connected maze.

    For a connected graph the number of independent cycles is
    ``edges - nodes + 1``; it is 0 for a perfect maze.
    """
    nodes = len(grid) * len(grid[0]) - len(blocked)
    return _count_passages(grid, blocked) - nodes + 1


def check_perfect(grid: Grid, blocked: set[Cell]) -> None:
    """Check that the maze is perfect: a connected maze without any loop."""
    loops = count_loops(grid, blocked)
    if loops != 0:
        raise MazeError(f"the maze is not perfect: it has {loops} loop(s)")


def _has_openable_wall(grid: Grid, cell: Cell, blocked: set[Cell]) -> bool:
    """Tell whether a closed wall of the cell faces a normal cell."""
    x, y = cell
    height = len(grid)
    width = len(grid[0])
    for direction in ALL_DIRECTIONS:
        if not grid[y][x] & direction:
            continue
        next_x = x + DELTA[direction][0]
        next_y = y + DELTA[direction][1]
        if (
            0 <= next_x < width
            and 0 <= next_y < height
            and (next_x, next_y) not in blocked
        ):
            return True
    return False


def count_dead_ends(grid: Grid, blocked: set[Cell]) -> int:
    """Count the dead-ends that could still be opened.

    A dead-end is a cell with a single opening. It is not counted when
    all its closed walls face the border or the '42' pattern, since no
    wall can be opened there.
    """
    count = 0
    for y, row in enumerate(grid):
        for x, walls in enumerate(row):
            if walls in _THREE_WALLS and (x, y) not in blocked:
                if _has_openable_wall(grid, (x, y), blocked):
                    count += 1
    return count


def _key_cells_problem(width: int, height: int, blocked: set[Cell]) -> bool:
    """Tell whether a corner or the centre is not an open corridor."""
    corners = {
        (0, 0),
        (width - 1, 0),
        (0, height - 1),
        (width - 1, height - 1),
    }
    if corners & blocked:
        return True
    xs = {width // 2} if width % 2 else {width // 2 - 1, width // 2}
    ys = {height // 2} if height % 2 else {height // 2 - 1, height // 2}
    centre = {(x, y) for x in xs for y in ys}
    return centre <= blocked


def playable_problems(
    grid: Grid,
    blocked: set[Cell],
    min_loops: int = 2,
    max_dead_ends: int = 2,
) -> list[str]:
    """List why a maze is not a good board for a Pac-Man-like game.

    The criteria are the ones of the analysis script: several independent
    routes, almost no dead-end, and open corners and centre.

    Returns:
        An empty list when the maze is a usable board.
    """
    problems = []
    height = len(grid)
    width = len(grid[0])

    loops = count_loops(grid, blocked)
    if loops < min_loops:
        problems.append(
            f"only {loops} independent route(s), {min_loops} wanted"
        )
    dead_ends = count_dead_ends(grid, blocked)
    if dead_ends > max_dead_ends:
        problems.append(
            f"{dead_ends} dead-ends, at most {max_dead_ends} wanted"
        )
    if _key_cells_problem(width, height, blocked):
        problems.append("a corner or the centre is not an open corridor")
    return problems


def check_all(
    grid: Grid, blocked: set[Cell], perfect: bool = False
) -> None:
    """Run every check of the subject.

    Args:
        grid: The wall grid.
        blocked: Coordinates of the cells forming the '42' pattern.
        perfect: Also check that the maze has no loop.
    """
    check_coherence(grid)
    check_border(grid)
    check_no_open3x3(grid)
    check_connectivity(grid, blocked)
    if perfect:
        check_perfect(grid, blocked)
