"""Main entry point for the A-Maze-ing maze generator."""

import sys

from config_parser import ConfigParser
from exporter import ExportError, save_maze
from mazegen.generator import MazeGenerator
from mazegen.solver import NoPathError, solve
from mazegen.validator import MazeError, check_all
from mazegen.visual_test import MazeVisualizer


def main() -> int:
    """Run the maze generation pipeline.

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

        generator = MazeGenerator(parser)
        grid = generator.generate()

        check_all(grid, generator.blocked)

        path = solve(grid, config["ENTRY"], config["EXIT"])

        output_file = config["OUTPUT_FILE"]
        save_maze(
            filepath=output_file,
            grid=grid,
            entry=config["ENTRY"],
            exit_cell=config["EXIT"],
            path=path,
        )

        print("Successfully generated maze ",
              f"({config['WIDTH']}x{config['HEIGHT']}) "
              f"-> {output_file} (path length: {len(path) - 1} steps)")
        visualizer = MazeVisualizer()
        visualizer.display(
            grid=grid,
            entry=config["ENTRY"],
            exit_=config["EXIT"],
            blocked=generator.blocked,
        )

        return 0

    except (MazeError, NoPathError, ExportError, ValueError) as err:
        print(f"Error: {err}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        return 130


if __name__ == "__main__":
    sys.exit(main())
