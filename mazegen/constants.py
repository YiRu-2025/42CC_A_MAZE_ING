"""Direction constants shared by the maze generator."""

# 单元格(x, y)，那么移动后的坐标就是 (x + dx, y + dy)。
# 二维数组 grid[row][col] 里，行是 y，列是 x，取值时记得对应 grid[y + dy][x + dx]

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
