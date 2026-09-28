"""Maze generation engine."""

import random
from typing import Iterator, Optional

from config_parser import ConfigParser

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


class MazeGenerator:
    """Generate a maze from a validated configuration."""

    def __init__(self, params: ConfigParser) -> None:
        """Initialize the maze generator."""
        self.params = params.config

        self.width: int = self.params["WIDTH"]
        self.height: int = self.params["HEIGHT"]
        self.entry: tuple[int, int] = self.params["ENTRY"]
        self.exit: tuple[int, int] = self.params["EXIT"]
        self.perfect: bool = self.params["PERFECT"]

        seed: Optional[int] = self.params.get("SEED")
        self.random = random.Random(seed)

        self.grid: list[list[int]] = []
        self.blocked: set[tuple[int, int]] = set()

    def generate(self) -> list[list[int]]:
        """Generate and return the maze grid."""
        self._create_grid()
        self._place_42()
        self._check_entry_exit()

        self._generate_perfect()

        if not self.perfect:
            self._generate_loops()

        return self.grid

    def _create_grid(self) -> None:
        """Create a grid where every cell initially has four walls."""
        self.grid = [
            [ALL_WALLS for _ in range(self.width)]
            for _ in range(self.height)
        ]

    def _place_42(self) -> None:
        """Place the centered '42' pattern as blocked cells."""
        if (
            self.width < PATTERN_WIDTH
            or self.height < PATTERN_HEIGHT
        ):
            return

        start_x = (self.width - PATTERN_WIDTH) // 2
        start_y = (self.height - PATTERN_HEIGHT) // 2

        for pattern_y, row in enumerate(PATTERN_42):
            for pattern_x, value in enumerate(row):
                if value == "X":
                    x = start_x + pattern_x
                    y = start_y + pattern_y
                    self.blocked.add((x, y))

    def _check_entry_exit(self) -> None:
        """Ensure entry and exit are not part of the blocked pattern."""
        if self.entry in self.blocked:
            raise ValueError("ENTRY is inside the '42' pattern")

        if self.exit in self.blocked:
            raise ValueError("EXIT is inside the '42' pattern")

    def _generate_perfect(self) -> None:
        """Generate a spanning tree using randomized depth-first search."""
        visited: set[tuple[int, int]] = {self.entry}
        stack: list[tuple[int, int]] = [self.entry]

        while stack:
            current = stack[-1]
            candidates = [
                position
                for position, _direction in self._neighbors(current)
                if position not in visited
                and position not in self.blocked
            ]

            if not candidates:
                stack.pop()
                continue

            next_cell = self.random.choice(candidates)
            direction = self._direction_between(current, next_cell)

            self._open_between(current, next_cell, direction)

            visited.add(next_cell)
            stack.append(next_cell)

        expected = self.width * self.height - len(self.blocked)

        if len(visited) != expected:
            raise ValueError(
                "the '42' pattern prevents the maze from being connected"
            )

    def _generate_loops(self) -> None:
        """Add extra passages while preventing open 3x3 areas."""
        walls = list(self._internal_walls())
        self.random.shuffle(walls)

        for first, second, direction in walls:
            if not self._can_open(first, second, direction):
                continue

            self._open_between(first, second, direction)

    def _neighbors(
        self,
        position: tuple[int, int],
    ) -> Iterator[tuple[tuple[int, int], int]]:
        """Yield valid neighboring cells and their direction."""
        x, y = position

        for direction in ALL_DIRECTIONS:
            dx, dy = DELTA[direction]
            next_x = x + dx
            next_y = y + dy

            if not self._inside(next_x, next_y):
                continue

            yield (next_x, next_y), direction

    def _internal_walls(
        self,
    ) -> Iterator[
        tuple[
            tuple[int, int],
            tuple[int, int],
            int,
        ]
    ]:
        """Yield every internal east and south wall."""
        for y in range(self.height):
            for x in range(self.width):
                current = (x, y)

                if x < self.width - 1:
                    right = (x + 1, y)
                    if (
                        current not in self.blocked
                        and right not in self.blocked
                    ):
                        yield current, right, EAST

                if y < self.height - 1:
                    below = (x, y + 1)
                    if (
                        current not in self.blocked
                        and below not in self.blocked
                    ):
                        yield current, below, SOUTH

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

        legal = not self._creates_open_3x3(first, second)

        self._close_between(first, second, direction)

        return legal

    def _creates_open_3x3(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
    ) -> bool:
        """Check whether an opening creates a completely open 3x3."""
        candidates = {
            (first[0] - dx, first[1] - dy)
            for dx in range(3)
            for dy in range(3)
        }

        candidates.update(
            {
                (second[0] - dx, second[1] - dy)
                for dx in range(3)
                for dy in range(3)
            }
        )

        for left, top in candidates:
            if self._is_open_3x3(left, top):
                return True

        return False

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

                if x < left + 2:
                    if self._has_wall((x, y), EAST):
                        return False

                if y < top + 2:
                    if self._has_wall((x, y), SOUTH):
                        return False

        return True

    def _open_between(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
        direction: int,
    ) -> None:
        """Open the shared wall between two adjacent cells."""
        opposite = OPPOSITE[direction]

        x1, y1 = first
        x2, y2 = second

        self.grid[y1][x1] &= ~direction
        self.grid[y2][x2] &= ~opposite

    def _close_between(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
        direction: int,
    ) -> None:
        """Close the shared wall between two adjacent cells."""
        opposite = OPPOSITE[direction]

        x1, y1 = first
        x2, y2 = second

        self.grid[y1][x1] |= direction
        self.grid[y2][x2] |= opposite

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

    def _direction_between(
        self,
        first: tuple[int, int],
        second: tuple[int, int],
    ) -> int:
        """Return the direction from first cell to second cell."""
        dx = second[0] - first[0]
        dy = second[1] - first[1]

        for direction, delta in DELTA.items():
            if delta == (dx, dy):
                return direction

        raise ValueError(
            f"cells {first} and {second} are not adjacent"
        )

def solve(self) -> list[tuple[int, int]]:
    """Return the shortest path from the entry to the exit."""
    return _solve(self.grid, self.entry, self.exit)
