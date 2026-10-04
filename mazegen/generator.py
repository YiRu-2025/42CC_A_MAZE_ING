"""Maze generation engine."""

import random
from collections.abc import Iterator
from typing import Optional

from .constants import (
    ALL_DIRECTIONS,
    DELTA,
    EAST,
    NORTH,
    OPPOSITE,
    SOUTH,
    WEST,
)
from .solver import solve as _solve
from .validator import playable_problems

_FOUR = (
    "X.X",
    "X.X",
    "XXX",
    "..X",
    "..X",
)

_TWO = (
    "XXX",
    "..X",
    "XXX",
    "X..",
    "XXX",
)

PATTERN_42 = tuple(f"{a}.{b}" for a, b in zip(_FOUR, _TWO))
PATTERN_WIDTH = 7
PATTERN_HEIGHT = 5

ALL_WALLS = NORTH | EAST | SOUTH | WEST

# Number of times the playable board is rebuilt when it misses a criterion.
SMALL_MAZE_ATTEMPTS = 10
LARGE_MAZE_ATTEMPTS = 2
LARGE_MAZE_CELLS = 10_000


class MazeGenerator:
    """Generate a maze with a hidden '42' pattern.

    Attributes:
        grid: One integer per cell, ``grid[y][x]``. A bit set to 1 means a
            closed wall: 1 north, 2 east, 4 south, 8 west.
        blocked: Coordinates of the cells that draw the '42' pattern.
        warnings: Messages about what could not be done as requested
            (pattern omitted, board criteria missed). The generator never
            prints, so the caller decides what to do with them.
        pattern_placed: Whether the '42' pattern is part of the maze.
    """

    def __init__(
        self,
        width: int,
        height: int,
        entry: tuple[int, int],
        exit_cell: tuple[int, int],
        perfect: bool = False,
        seed: Optional[int] = None,
        openness: float = 1.0,
    ) -> None:
        """Initialize the maze generator.

        Args:
            width: Number of cells horizontally (at least 2).
            height: Number of cells vertically (at least 2).
            entry: Entry cell (x, y).
            exit_cell: Exit cell (x, y), different from the entry.
            perfect: True for a maze with a single path and no loop.
            seed: Seed of the random generator, for reproducible mazes.
            openness: Between 0 and 1. Share of the legal extra passages
                that are opened when ``perfect`` is False. 1 opens all of
                them, which gives the most connected board.
        """
        if width < 2 or height < 2:
            raise ValueError("width and height must be at least 2")
        if not 0.0 <= openness <= 1.0:
            raise ValueError("openness must be between 0 and 1")
        self._check_inside(entry, "ENTRY", width, height)
        self._check_inside(exit_cell, "EXIT", width, height)
        if entry == exit_cell:
            raise ValueError("ENTRY and EXIT must be different cells")

        self.width = width
        self.height = height
        self.entry = entry
        self.exit = exit_cell
        self.perfect = perfect
        self.openness = openness
        self.random = random.Random(seed)

        self.grid: list[list[int]] = []
        self.blocked: set[tuple[int, int]] = set()
        self.warnings: list[str] = []
        self.pattern_placed = False

    @staticmethod
    def _check_inside(
        cell: tuple[int, int],
        name: str,
        width: int,
        height: int,
    ) -> None:
        """Check that a cell is inside the maze."""
        x, y = cell
        if not (0 <= x < width and 0 <= y < height):
            raise ValueError(
                f"{name} ({x},{y}) is outside the maze "
                f"(x: 0-{width - 1}, y: 0-{height - 1})"
            )

    # -- public API -------------------------------------------------------
    def generate(self) -> list[list[int]]:
        """Generate the maze and return its grid."""
        self.warnings = []
        self.blocked = set()
        self.pattern_placed = self._place_42()
        if not self.pattern_placed:
            self.warnings.append(
                "the maze is too small for the '42' pattern: it is omitted"
            )
        self._check_entry_exit()

        self._create_grid()
        if not self._carve_spanning_tree():
            # The pattern cuts the maze in several parts: draw without it.
            self.blocked = set()
            self.pattern_placed = False
            self.warnings.append(
                "the '42' pattern disconnects this maze: it is omitted"
            )
            self._create_grid()
            self._carve_spanning_tree()

        if not self.perfect:
            self._make_playable()
        return self.grid

    def solve(self) -> list[tuple[int, int]]:
        """Return the shortest path from the entry to the exit."""
        return _solve(self.grid, self.entry, self.exit)

    # -- building blocks --------------------------------------------------
    def _create_grid(self) -> None:
        """Create a grid where every cell initially has four walls."""
        self.grid = [
            [ALL_WALLS] * self.width for _ in range(self.height)
        ]

    def _place_42(self) -> bool:
        """Place the centered '42' pattern as blocked cells.

        Returns:
            False when the maze is too small to hold the pattern.
        """
        if self.width < PATTERN_WIDTH or self.height < PATTERN_HEIGHT:
            return False

        start_x = (self.width - PATTERN_WIDTH) // 2
        start_y = (self.height - PATTERN_HEIGHT) // 2

        for pattern_y, row in enumerate(PATTERN_42):
            for pattern_x, value in enumerate(row):
                if value == "X":
                    x = start_x + pattern_x
                    y = start_y + pattern_y
                    self.blocked.add((x, y))
        return True

    def _check_entry_exit(self) -> None:
        """Ensure entry and exit are not part of the blocked pattern."""
        if self.entry in self.blocked:
            raise ValueError("ENTRY is inside the '42' pattern")

        if self.exit in self.blocked:
            raise ValueError("EXIT is inside the '42' pattern")

    def _carve_spanning_tree(self) -> bool:
        """Carve a spanning tree with a randomized depth-first search.

        The search uses an explicit stack instead of recursion, so a large
        maze cannot exceed the recursion limit.

        Returns:
            False when some free cells could not be reached.
        """
        visited: set[tuple[int, int]] = {self.entry}
        stack: list[tuple[int, int]] = [self.entry]

        while stack:
            current = stack[-1]
            candidates = [
                (position, direction)
                for position, direction in self._neighbors(current)
                if position not in visited and position not in self.blocked
            ]

            if not candidates:
                stack.pop()
                continue

            next_cell, direction = self.random.choice(candidates)
            self._open_between(current, next_cell, direction)
            visited.add(next_cell)
            stack.append(next_cell)

        return len(visited) == self.width * self.height - len(self.blocked)

    def _make_playable(self) -> None:
        """Turn the spanning tree into a board for a Pac-Man-like game.

        Extra passages are opened wherever no 3x3 area becomes open. This
        removes almost every dead-end and creates many independent loops.
        The result is checked against the playable-board criteria; when a
        criterion is missed, the extra passages are drawn again from the
        same tree, which is cheap compared with carving a new one.
        """
        tree = [row[:] for row in self.grid]
        cells = self.width * self.height
        attempts = (
            SMALL_MAZE_ATTEMPTS
            if cells <= LARGE_MAZE_CELLS
            else LARGE_MAZE_ATTEMPTS
        )

        problems: list[str] = []
        for _ in range(attempts):
            self.grid = [row[:] for row in tree]
            self._generate_loops()
            problems = playable_problems(self.grid, self.blocked)
            if not problems:
                return

        self.warnings.append(
            "the board does not fully meet the playable criteria: "
            + "; ".join(problems)
        )

    def _generate_loops(self) -> None:
        """Add extra passages while preventing open 3x3 areas."""
        walls = list(self._internal_walls())
        self.random.shuffle(walls)

        for first, second, direction in walls:
            if self.openness < 1.0 and self.random.random() >= self.openness:
                continue
            if self._can_open(first, second, direction):
                self._open_between(first, second, direction)

    def _neighbors(
        self,
        position: tuple[int, int],
    ) -> Iterator[tuple[tuple[int, int], int]]:
        """Yield valid neighboring cells and their direction."""
        x, y = position

        for direction in ALL_DIRECTIONS:
            dx, dy = DELTA[direction]
            if self._inside(x + dx, y + dy):
                yield (x + dx, y + dy), direction

    def _internal_walls(
        self,
    ) -> Iterator[tuple[tuple[int, int], tuple[int, int], int]]:
        """Yield every internal east and south wall between free cells."""
        for y in range(self.height):
            for x in range(self.width):
                current = (x, y)
                if current in self.blocked:
                    continue

                if x < self.width - 1 and (x + 1, y) not in self.blocked:
                    yield current, (x + 1, y), EAST

                if y < self.height - 1 and (x, y + 1) not in self.blocked:
                    yield current, (x, y + 1), SOUTH

    def _can_open(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
        direction: int,
    ) -> bool:
        """Return whether opening a wall keeps the maze valid."""
        if not self._has_wall(first, direction):
            return False

        self._open_between(first, second, direction)
        legal = not self._creates_open_3x3(first, direction)
        self._close_between(first, second, direction)
        return legal

    def _creates_open_3x3(
        self,
        first: tuple[int, int],
        direction: int,
    ) -> bool:
        """Check whether the wall just opened makes a 3x3 area open.

        Only the 3x3 areas that contain both cells of the wall can change,
        so six areas are tested, not every area around the two cells.
        """
        x, y = first
        lefts: tuple[int, ...]
        tops: tuple[int, ...]
        if direction == EAST:
            lefts = (x - 1, x)
            tops = (y - 2, y - 1, y)
        else:
            lefts = (x - 2, x - 1, x)
            tops = (y - 1, y)

        return any(
            self._is_open_3x3(left, top) for left in lefts for top in tops
        )

    def _is_open_3x3(self, left: int, top: int) -> bool:
        """Return whether the given 3x3 area is completely open."""
        if (
            left < 0
            or top < 0
            or left + 2 >= self.width
            or top + 2 >= self.height
        ):
            return False

        for y in range(top, top + 3):
            for x in range(left, left + 3):
                if (x, y) in self.blocked:
                    return False
                if x < left + 2 and self._has_wall((x, y), EAST):
                    return False
                if y < top + 2 and self._has_wall((x, y), SOUTH):
                    return False
        return True

    def _open_between(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
        direction: int,
    ) -> None:
        """Open the shared wall between two adjacent cells."""
        x1, y1 = first
        x2, y2 = second
        self.grid[y1][x1] &= ~direction
        self.grid[y2][x2] &= ~OPPOSITE[direction]

    def _close_between(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
        direction: int,
    ) -> None:
        """Close the shared wall between two adjacent cells."""
        x1, y1 = first
        x2, y2 = second
        self.grid[y1][x1] |= direction
        self.grid[y2][x2] |= OPPOSITE[direction]

    def _has_wall(
        self,
        position: tuple[int, int],
        direction: int,
    ) -> bool:
        """Return whether a cell has the given wall."""
        x, y = position
        return bool(self.grid[y][x] & direction)

    def _inside(self, x: int, y: int) -> bool:
        """Return whether coordinates are inside the maze."""
        return 0 <= x < self.width and 0 <= y < self.height
