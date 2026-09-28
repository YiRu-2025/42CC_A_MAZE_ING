"""Terminal visualization for the generated maze."""

from .constants import EAST, NORTH, SOUTH


class MazeVisualizer:
    """Display a maze as ASCII art in the terminal."""

    def display(
        self,
        grid: list[list[int]],
        entry: tuple[int, int],
        exit_: tuple[int, int],
        blocked: set[tuple[int, int]],
    ) -> None:
        """Print the complete maze."""
        if not grid:
            return

        height = len(grid)
        width = len(grid[0])

        self._print_top_border(grid, width)

        for y in range(height):
            self._print_cell_row(
                grid,
                y,
                width,
                entry,
                exit_,
                blocked,
            )
            self._print_horizontal_walls(grid, y, width)

    def _print_top_border(
        self,
        grid: list[list[int]],
        width: int,
    ) -> None:
        """Print the top border of the maze."""
        line = ""

        for x in range(width):
            if grid[0][x] & NORTH:
                line += "+---"
            else:
                line += "+   "

        line += "+"

        print(line)

    def _print_cell_row(
        self,
        grid: list[list[int]],
        y: int,
        width: int,
        entry: tuple[int, int],
        exit_: tuple[int, int],
        blocked: set[tuple[int, int]],
    ) -> None:
        """Print one row of cells and their vertical walls."""
        line = ""

        for x in range(width):
            line += self._cell_content(
                x,
                y,
                entry,
                exit_,
                blocked,
            )

            if grid[y][x] & EAST:
                line += "|"
            else:
                line += " "

        print(line)

    def _print_horizontal_walls(
        self,
        grid: list[list[int]],
        y: int,
        width: int,
    ) -> None:
        """Print the south walls below a row."""
        line = ""

        for x in range(width):
            if grid[y][x] & SOUTH:
                line += "+---"
            else:
                line += "+   "

        line += "+"

        print(line)

    def _cell_content(
        self,
        x: int,
        y: int,
        entry: tuple[int, int],
        exit_: tuple[int, int],
        blocked: set[tuple[int, int]],
    ) -> str:
        """Return the content displayed inside one cell."""
        if (x, y) == entry:
            return " S "

        if (x, y) == exit_:
            return " E "

        if (x, y) in blocked:
            return "42 "

        return "   "
