"""Write a generated maze to the output file required by the subject.

The file holds one hexadecimal digit per cell, then an empty line, then
three lines: the entry coordinates, the exit coordinates and the
shortest path written with the letters N, E, S and W.
"""

from mazegen.solver import path_to_letters


class ExportError(Exception):
    """Raised when the maze cannot be written to disk."""


def format_maze(
    grid: list[list[int]],
    entry: tuple[int, int],
    exit_cell: tuple[int, int],
    path: list[tuple[int, int]],
) -> str:
    """Build the whole content of the output file."""
    lines = ["".join(f"{cell:X}" for cell in row) for row in grid]
    lines.append("")
    lines.append(f"{entry[0]},{entry[1]}")
    lines.append(f"{exit_cell[0]},{exit_cell[1]}")
    lines.append(path_to_letters(path))
    return "".join(line + "\n" for line in lines)


def save_maze(
    filepath: str,
    grid: list[list[int]],
    entry: tuple[int, int],
    exit_cell: tuple[int, int],
    path: list[tuple[int, int]],
) -> None:
    """Write the maze to a file."""
    content = format_maze(grid, entry, exit_cell, path)
    try:
        with open(filepath, "w", encoding="utf-8", newline="\n") as f:
            f.write(content)
    except OSError as e:
        raise ExportError(f"cannot write '{filepath}': {e.strerror}") from None
