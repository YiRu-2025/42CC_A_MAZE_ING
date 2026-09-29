"""Main entry point for the A-Maze-ing maze generator."""

import sys

from config_parser import ConfigParser
from exporter import ExportError, save_maze
from mazegen.generator import MazeGenerator
from mazegen.solver import NoPathError, solve
from mazegen.validator import MazeError, check_all
from typing import Any
from visualizer import MazeVisualizer


def _generate_and_solve(
    config: dict[str, Any], use_seed: bool
) -> tuple[MazeGenerator, list[list[int]], list[tuple[int, int]]]:
    """Generate one maze, validate it and solve it.

    Args:
        config: The validated configuration dictionary.
        use_seed: Whether to honor an optional SEED from the config file.
            Regenerating on demand ("1" in the menu) always draws a fresh
            maze, so it ignores SEED even if the file sets one; the very
            first maze of the run still respects it, for reproducibility.

    Returns:
        The (generator, grid, path) produced.

    Raises:
        MazeError, NoPathError, ValueError: on an invalid configuration
        or an unsolvable/incoherent maze.
    """
    generator = MazeGenerator(
        width=config["WIDTH"],
        height=config["HEIGHT"],
        entry=config["ENTRY"],
        exit_cell=config["EXIT"],
        perfect=config["PERFECT"],
        seed=config.get("SEED") if use_seed else None,
    )
    grid = generator.generate()
    check_all(grid, generator.blocked)
    path = solve(grid, config["ENTRY"], config["EXIT"])
    return generator, grid, path


def _save_and_announce(
    config: dict[str, Any],
    grid: list[list[int]],
    path: list[tuple[int, int]],
) -> None:
    """Write the maze to its output file and print the success line."""
    save_maze(
        filepath=config["OUTPUT_FILE"],
        grid=grid,
        entry=config["ENTRY"],
        exit_cell=config["EXIT"],
        path=path,
    )
    print(
        f"Successfully generated maze ({config['WIDTH']}x{config['HEIGHT']})"
        f" -> {config['OUTPUT_FILE']} (path length: {len(path) - 1} steps)"
    )


def main() -> int:
    """Run the maze generation pipeline with its interactive menu.

    Returns:
        0 on success, non-zero integer on error.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>", file=sys.stderr)
        return 1

    config_path = sys.argv[1]

    try:
        parser = ConfigParser(config_path)
        config = parser.parse()

        generator, grid, path = _generate_and_solve(config, use_seed=True)
        _save_and_announce(config, grid, path)

        visualizer = MazeVisualizer()

        while True:
            visualizer.display(
                grid=grid,
                entry=config["ENTRY"],
                exit_=config["EXIT"],
                blocked=generator.blocked,
                path=path,
            )

            action = visualizer.run_menu()
            if action == "quit":
                return 0

            if action == "regenerate":
                try:
                    generator, grid, path = _generate_and_solve(
                        config, use_seed=False
                    )  # noqa E1501
                except (MazeError, NoPathError, ValueError) as err:
                    print(
                        f"Error: {err} (keeping the previous maze)", file=sys.stderr  # noqa: E501
                    )  # noqa E1501
                    continue
                try:
                    _save_and_announce(config, grid, path)
                except ExportError as err:
                    print(f"Error: {err}", file=sys.stderr)
                    return 1
            # any other action (path toggled, colors rotated) just redraws
            # the same maze on the next loop iteration.

    except (MazeError, NoPathError, ExportError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
