"""Interactive terminal visualizer for the maze program.

This module is part of the program, not of the reusable ``mazegen``
package: it prints to the terminal and reads keyboard input, which the
package itself is never allowed to do (see the project README).

It draws the maze as ASCII art -- walls, the entry, the exit and,
optionally, the shortest path -- and drives the interactive menu that
lets the user regenerate the maze, show or hide the path, and rotate
the colors used for the walls and for the "42" pattern.
"""

from mazegen.constants import NORTH, EAST, SOUTH

RESET = "\033[0m"
BOLD = "\033[1m"

# Colors the walls cycle through, selected with menu option 3.
WALL_COLORS = [
    ("default", "\033[37m"),
    ("cyan", "\033[36m"),
    ("yellow", "\033[33m"),
    ("magenta", "\033[35m"),
    ("blue", "\033[34m"),
    ("green", "\033[32m"),
]

# Colors the "42" pattern cycles through, selected with menu option 4.
PATTERN_COLORS = [
    ("red", "\033[91m"),
    ("magenta", "\033[95m"),
    ("cyan", "\033[96m"),
    ("yellow", "\033[93m"),
]

ENTRY_COLOR = "\033[92m"   # bright green, cell marked "S"
EXIT_COLOR = "\033[91m"    # bright red, cell marked "E"
PATH_COLOR = "\033[93m"    # bright yellow dots

MENU = """
------------------------------------
 1) Re-generate a new maze
 2) Show / hide the shortest path
 3) Rotate the wall colors
 4) Rotate the '42' pattern colors
 5) Quit
------------------------------------
Choice: """


class MazeVisualizer:
    """Draw a maze in the terminal and hold the interactive display state.

    The generated maze itself is never touched here: this class only
    reads ``grid``/``entry``/``exit_``/``blocked``/``path`` and turns
    them into colored ASCII art, plus the small text menu that drives
    the interactions required by the subject.
    """

    def __init__(self) -> None:
        self.show_path = True
        self._wall_color_idx = 0
        self._pattern_color_idx = 0

    # -- state changes used by the menu -------------------------------
    def toggle_path(self) -> None:
        """Flip whether the shortest path is drawn."""
        self.show_path = not self.show_path

    def rotate_wall_color(self) -> str:
        """Switch to the next wall color and return its name."""
        self._wall_color_idx = (self._wall_color_idx + 1) % len(WALL_COLORS)
        return WALL_COLORS[self._wall_color_idx][0]

    def rotate_pattern_color(self) -> str:
        """Switch to the next '42' pattern color and return its name."""
        self._pattern_color_idx = (
            (self._pattern_color_idx + 1) % len(PATTERN_COLORS))
        return PATTERN_COLORS[self._pattern_color_idx][0]

    @property
    def _wall_color(self) -> str:
        return WALL_COLORS[self._wall_color_idx][1]

    @property
    def _pattern_color(self) -> str:
        return PATTERN_COLORS[self._pattern_color_idx][1]

    # -- drawing --------------------------------------------------------
    def display(
        self,
        grid: list[list[int]],
        entry: tuple[int, int],
        exit_: tuple[int, int],
        blocked: set[tuple[int, int]],
        path: list[tuple[int, int]] | None,
    ) -> None:
        """Print the whole maze once, using the current display state."""
        if not grid:
            return

        height = len(grid)
        width = len(grid[0])
        path_cells = set(path) if (self.show_path and path) else set()

        self._print_top_border(grid, width)
        for y in range(height):
            self._print_cell_row(grid, y, width, entry,
                                 exit_, blocked, path_cells)
            self._print_horizontal_walls(grid, y, width)

    def _print_top_border(
        self, grid: list[list[int]], width: int
    ) -> None:
        wc = self._wall_color
        line = ""
        for x in range(width):
            line += (f"{wc}+---{RESET}"
                     if grid[0][x] & NORTH else f"{wc}+{RESET}   ")
        line += f"{wc}+{RESET}"
        print(line)

    def _print_cell_row(
        self,
        grid: list[list[int]],
        y: int,
        width: int,
        entry: tuple[int, int],
        exit_: tuple[int, int],
        blocked: set[tuple[int, int]],
        path_cells: set[tuple[int, int]],
    ) -> None:
        wc = self._wall_color
        line = ""
        for x in range(width):
            line += self._cell_content((x, y), entry, exit_, blocked, path_cells)  # noqa E501
            line += f"{wc}|{RESET}" if grid[y][x] & EAST else " "
        print(line)

    def _print_horizontal_walls(
        self, grid: list[list[int]], y: int, width: int
    ) -> None:
        wc = self._wall_color
        line = ""
        for x in range(width):
            line += f"{wc}+---{RESET}" if grid[y][x] & SOUTH else f"{wc}+{RESET}   " # noqa E501
        line += f"{wc}+{RESET}"
        print(line)

    def _cell_content(
        self,
        cell: tuple[int, int],
        entry: tuple[int, int],
        exit_: tuple[int, int],
        blocked: set[tuple[int, int]],
        path_cells: set[tuple[int, int]],
    ) -> str:
        if cell == entry:
            return f"{ENTRY_COLOR}{BOLD} S {RESET}"
        if cell == exit_:
            return f"{EXIT_COLOR}{BOLD} E {RESET}"
        if cell in blocked:
            return f"{self._pattern_color}{BOLD}42 {RESET}"
        if cell in path_cells:
            return f"{PATH_COLOR} . {RESET}"
        return "   "

    # -- interactive menu -------------------------------------------------
    def run_menu(self) -> str | None:
        """Read one menu choice, run the matching callback, and report it.

        Options "2", "3" and "4" are handled here and return None, so
        the caller only redraws. Options "1" and "5" are reported back
        as "regenerate" and "quit", because they rebuild or stop the
        whole pipeline.
        """
        choice = input(MENU).strip()

        if choice == "1":
            return "regenerate"
        if choice == "2":
            self.toggle_path()
            state = "shown" if self.show_path else "hidden"
            print(f"-> shortest path {state}")
            return None
        if choice == "3":
            name = self.rotate_wall_color()
            print(f"-> wall color: {name}")
            return None
        if choice == "4":
            name = self.rotate_pattern_color()
            print(f"-> '42' pattern color: {name}")
            return None
        if choice == "5":
            return "quit"

        print("-> invalid choice, please enter 1-5")
        return None
