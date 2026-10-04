"""Direction constants shared by the maze generator.

A cell (x, y) moved in a direction (dx, dy) becomes (x + dx, y + dy).
In the two-dimensional grid the row is y and the column is x, so the
neighbour is read with grid[y + dy][x + dx].
"""

NORTH = 1
EAST = 2
SOUTH = 4
WEST = 8

ALL_DIRECTIONS = (NORTH, EAST, SOUTH, WEST)

DELTA = {
    NORTH: (0, -1),
    EAST: (1, 0),
    SOUTH: (0, 1),
    WEST: (-1, 0),
}

OPPOSITE = {
    NORTH: SOUTH,
    SOUTH: NORTH,
    EAST: WEST,
    WEST: EAST,
}

LETTER = {
    NORTH: "N",
    EAST: "E",
    SOUTH: "S",
    WEST: "W",
}
