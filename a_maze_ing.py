"""Main entry point for the A-Maze-ing maze generator."""

import sys
from typing import Any

from config_parser import ConfigParser
from exporter import ExportError, save_maze
from mazegen.generator import MazeGenerator
from mazegen.solver import NoPathError, solve
from mazegen.validator import MazeError, check_all
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
    for warning in generator.warnings:
        print(f"Warning: {warning}", file=sys.stderr)
    check_all(grid, generator.blocked, perfect=config["PERFECT"])
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


def _run_menu(
    config: dict[str, Any],
    generator: MazeGenerator,
    grid: list[list[int]],
    path: list[tuple[int, int]],
) -> None:
    """Draw the maze and handle the menu until the user quits."""
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
            return

        if action == "regenerate":
            try:
                generator, grid, path = _generate_and_solve(
                    config, use_seed=False
                )
            except (MazeError, NoPathError, ValueError) as err:
                print(
                    f"Error: {err} (keeping the previous maze)",
                    file=sys.stderr,
                )
                continue
            _save_and_announce(config, grid, path)
        # any other action (path toggled, colors rotated) just redraws
        # the same maze on the next loop iteration.


def main() -> int:
    """Run the maze generation pipeline with its interactive menu.

    Returns:
        0 on success, non-zero integer on error.
    """
    if len(sys.argv) != 2:
        print("Usage: python3 a_maze_ing.py <config_file>", file=sys.stderr)
        return 1

    try:
        config = ConfigParser(sys.argv[1]).parse()
        generator, grid, path = _generate_and_solve(config, use_seed=True)
        _save_and_announce(config, grid, path)
        _run_menu(config, generator, grid, path)
        return 0
    except (MazeError, NoPathError, ExportError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130
    except Exception as err:  # the program must never crash with a trace
        print(f"Unexpected error: {err}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
