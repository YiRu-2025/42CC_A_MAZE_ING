"""Unit tests of the maze generator, the parser and the exporter."""

from pathlib import Path

import pytest

import maze_analyzer
from config_parser import ConfigError, ConfigParser
from exporter import format_maze
from mazegen import MazeError, MazeGenerator, check_all, solve
from mazegen.validator import count_loops

SIZES = [(5, 5), (9, 9), (10, 10), (20, 15), (21, 15), (40, 30)]
CONFIG = (
    "WIDTH=20\nHEIGHT=15\nENTRY=0,0\nEXIT=19,14\n"
    "OUTPUT_FILE=maze.txt\nPERFECT=True\n"
)


def make(
    width: int, height: int, perfect: bool, seed: int
) -> MazeGenerator:
    """Generate a maze between two opposite corners."""
    maze = MazeGenerator(
        width, height, (0, 0), (width - 1, height - 1), perfect, seed
    )
    maze.generate()
    return maze


def analyze(maze: MazeGenerator, tmp_path: Path) -> str:
    """Write a maze and return the verdict of the analysis script."""
    path = tmp_path / "maze.txt"
    path.write_text(
        format_maze(maze.grid, maze.entry, maze.exit, maze.solve())
    )
    report = maze_analyzer.analyze(maze_analyzer.Maze.from_file(str(path)))
    return maze_analyzer.verdict(report, 2, 2)


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("seed", range(5))
def test_perfect_maze_has_no_loop(size: tuple[int, int], seed: int) -> None:
    maze = make(*size, True, seed)
    check_all(maze.grid, maze.blocked, perfect=True)
    assert count_loops(maze.grid, maze.blocked) == 0


@pytest.mark.parametrize("size", SIZES)
@pytest.mark.parametrize("seed", range(5))
def test_playable_maze_is_usable(
    size: tuple[int, int], seed: int, tmp_path: Path
) -> None:
    maze = make(*size, False, seed)
    check_all(maze.grid, maze.blocked)
    assert not any("playable" in w for w in maze.warnings)
    assert analyze(maze, tmp_path).startswith("Pac-Man-USABLE")


def test_perfect_maze_is_judged_perfect(tmp_path: Path) -> None:
    maze = make(20, 15, True, 3)
    assert analyze(maze, tmp_path).startswith("PERFECT maze")


def test_same_seed_gives_same_maze() -> None:
    assert make(20, 15, False, 7).grid == make(20, 15, False, 7).grid
    assert make(20, 15, False, 7).grid != make(20, 15, False, 8).grid


def test_pattern_42_is_closed_and_visible() -> None:
    maze = make(20, 15, False, 1)
    assert maze.pattern_placed
    assert len(maze.blocked) == 20
    assert all(maze.grid[y][x] == 15 for x, y in maze.blocked)


def test_small_maze_omits_the_pattern_with_a_warning() -> None:
    maze = make(6, 6, True, 1)
    assert not maze.pattern_placed
    assert maze.blocked == set()
    assert maze.warnings


def test_entry_inside_the_pattern_is_refused() -> None:
    maze = MazeGenerator(20, 15, (6, 5), (19, 14))
    with pytest.raises(ValueError):
        maze.generate()


def test_path_goes_from_entry_to_exit() -> None:
    maze = make(20, 15, False, 2)
    path = solve(maze.grid, maze.entry, maze.exit)
    assert path[0] == maze.entry and path[-1] == maze.exit
    assert path == maze.solve()


def test_validator_detects_a_wall_mismatch() -> None:
    maze = make(10, 10, True, 1)
    maze.grid[0][0] ^= 2
    with pytest.raises(MazeError):
        check_all(maze.grid, maze.blocked)


def test_output_format() -> None:
    maze = make(10, 10, True, 1)
    text = format_maze(maze.grid, maze.entry, maze.exit, maze.solve())
    lines = text.split("\n")
    assert text.endswith("\n")
    assert all(len(line) == 10 for line in lines[:10])
    assert lines[10] == ""
    assert lines[11:13] == ["0,0", "9,9"]


def write_config(tmp_path: Path, text: str) -> str:
    path = tmp_path / "config.txt"
    path.write_text(text)
    return str(path)


def test_valid_config(tmp_path: Path) -> None:
    text = "# comment\n\nseed = 5\n" + CONFIG
    config = ConfigParser(write_config(tmp_path, text)).parse()
    assert config["WIDTH"] == 20 and config["SEED"] == 5
    assert config["ENTRY"] == (0, 0) and config["PERFECT"] is True


@pytest.mark.parametrize(
    "text",
    [
        "WIDTH 20\n",
        CONFIG + "FOO=1\n",
        CONFIG + "WIDTH=5\n",
        CONFIG.replace("WIDTH=20", "WIDTH=abc"),
        CONFIG.replace("WIDTH=20", "WIDTH=5000"),
        CONFIG.replace("EXIT=19,14", "EXIT=0,0"),
        CONFIG.replace("EXIT=19,14", "EXIT=20,14"),
        CONFIG.replace("PERFECT=True", "PERFECT=maybe"),
        CONFIG.replace("OUTPUT_FILE=maze.txt", "OUTPUT_FILE="),
        CONFIG.replace("PERFECT=True\n", ""),
    ],
)
def test_invalid_config(tmp_path: Path, text: str) -> None:
    with pytest.raises(ConfigError):
        ConfigParser(write_config(tmp_path, text)).parse()


def test_missing_config_file(tmp_path: Path) -> None:
    with pytest.raises(ConfigError):
        ConfigParser(str(tmp_path / "nothing.txt")).parse()
