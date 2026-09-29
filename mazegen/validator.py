from .constants import NORTH, EAST, SOUTH, WEST


class MazeError(Exception):
    """Raised when a generated maze breaks one of the subject's rules."""


def has_wall(grid: list[list[int]], x: int, y: int, direction: int) -> bool:
    """Tell whether a cell has a wall"""
    return bool(grid[y][x] & direction)


def check_coherence(grid: list[list[int]]) -> None:
    """Check that 2 neighbours agree about the wall they share.
    Only the east and south sides are tested, because every shared wall
    is then looked at exactly once.
    """
    height = len(grid)
    width = len(grid[0])

    for y in range(height):
        for x in range(width):
            if x < width - 1:
                wallshare1 = has_wall(grid, x, y, EAST)
                wallshare2 = has_wall(grid, x + 1, y, WEST)
                if wallshare1 != wallshare2:
                    raise MazeError(
                        f"wall mismatch between ({x},{y}) east "
                        f"and ({x + 1},{y}) west"
                    )
            if y < height - 1:
                wallshare1 = has_wall(grid, x, y, SOUTH)
                wallshare2 = has_wall(grid, x, y + 1, NORTH)
                if wallshare1 != wallshare2:
                    raise MazeError(
                        f"wall mismatch between ({x},{y + 1}) south "
                        f"and ({y + 1},{y}) north"
                    )


def check_border(grid: list[list[int]]) -> None:
    """Check that the outer border of the maze is fully closed."""
    height = len(grid)
    width = len(grid[0])

    for x in range(width):
        if not has_wall(grid, x, 0, NORTH):
            raise MazeError(f"cell ({x},0) is open to the north border")
        if not has_wall(grid, x, height - 1, SOUTH):
            raise MazeError(f"cell ({x},{height - 1}) is open to the south border")  # noqa:E501
    for y in range(height):
        if not has_wall(grid, 0, y, WEST):
            raise MazeError(f"cell (0,{y}) is open to the west border")
        if not has_wall(grid, width - 1, y, EAST):
            raise MazeError(f"cell ({width - 1},{y}) is open to the east border")  # noqa:E501


def _is_open_block(grid: list[list[int]], left: int, top: int) -> bool:
    """Tell whether the 3x3 area with this top-left corner is fully open."""
    for y in range(top, top + 3):
        for x in range(left, left + 3):
            if x < left + 2 and has_wall(grid, x, y, EAST):
                return False
            if y < top + 2 and has_wall(grid, x, y, SOUTH):
                return False
    return True


def check_no_open3x3(grid: list[list[int]]) -> None:
    """Check that no 3x3 area of the maze is completely open."""
    height = len(grid)
    width = len(grid[0])
    for top in range(height - 2):
        for left in range(width - 2):
            if _is_open_block(grid, left, top):
                raise MazeError(f"3x3 open area starting at ({left},{top})")


def check_connectivity(grid: list[list[int]], blocked: set[tuple[int, int]]) -> None:  # noqa:E501
    """Check that every cell can be reached, except the '42' pattern.

    A flood fill is started from the first cell that is not part of the
    pattern, and the number of visited cells is compared with the number
    of cells that should be reachable.

    blocked: Coordinates of the cells forming the '42' pattern.
    """
    height = len(grid)
    width = len(grid[0])
    start = None
    for y in range(height):
        for x in range(width):
            if (x, y) not in blocked:
                start = (x, y)
                break
        if start is not None:
            break
    if start is None:
        raise MazeError("every cell belongs to the '42' pattern")
    seen = {start}
    stack = [start]
    while stack:
        x, y = stack.pop()

        if y > 0 and not has_wall(grid, x, y, NORTH) and (x, y - 1) not in seen:  # noqa:E501
            seen.add((x, y - 1))
            stack.append((x, y - 1))
        if (
            y < height - 1
            and not has_wall(grid, x, y, SOUTH)
            and (x, y + 1) not in seen
        ):
            seen.add((x, y + 1))
            stack.append((x, y + 1))
        if x > 0 and not has_wall(grid, x, y, WEST) and (x - 1, y) not in seen:
            seen.add((x - 1, y))
            stack.append((x - 1, y))
        if x < width - 1 and not has_wall(grid, x, y, EAST) and (x + 1, y) not in seen:  # noqa:E501
            seen.add((x + 1, y))
            stack.append((x + 1, y))

    expected = width * height - len(blocked)
    if len(seen) != expected:
        raise MazeError(
            f"maze is not fully connected: {len(seen)} cells reachable "
            f"out of {expected}"
        )


def check_all(grid: list[list[int]], blocked: set[tuple[int, int]]) -> None:  # noqa:E501
    """Check all the error situation"""
    check_coherence(grid)
    check_border(grid)
    check_no_open3x3(grid)
    check_connectivity(grid, blocked)
