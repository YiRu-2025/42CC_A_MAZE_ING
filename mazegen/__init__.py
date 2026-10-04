"""A-Maze-ing generator module.

Provides the MazeGenerator class, which builds perfect mazes and boards
playable by a Pac-Man-like game, plus a solver and validation helpers.
"""

from .constants import EAST, NORTH, SOUTH, WEST
from .generator import MazeGenerator
from .solver import NoPathError, path_to_letters, solve
from .validator import MazeError, check_all

__all__ = [
    "EAST",
    "MazeError",
    "MazeGenerator",
    "NORTH",
    "NoPathError",
    "SOUTH",
    "WEST",
    "check_all",
    "path_to_letters",
    "solve",
]
