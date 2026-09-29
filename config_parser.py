import sys
from typing import Any


class ConfigParser:
    """Parse and validate the configuration file of the maze generator."""

    REQUIRED_KEYS = {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}  # noqa:E501

    def __init__(self, filepath: str) -> None:
        """Store the config file path and prepare an empty dictionary.

        Args:
            filepath: Path to the configuration file.
        """

        self.filepath = filepath
        self.config: dict[str, Any] = {}

    def parse(self) -> dict[str, Any]:
        """Read the file, skip comments, then parse and validate KEY=VALUE.

        Returns:
            A dictionary of validated values, already converted to the
            right types (int, tuple, bool).

        Note:
            On any error, prints a message to stderr and exits with code 1.
        """

        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue

                    if "=" not in line:
                        raise ValueError(f"missing '=' in line: {line}")

                    key, value = line.split("=", 1)
                    key = key.strip().upper()
                    value = value.strip()

                    if key == "":
                        raise ValueError(f"empty key in line: {line}")
                    if key in self.config:
                        raise ValueError(f"duplicate key: {key}")

                    self.config[key] = value

            self._validate_and_cast()
            return self.config

        except FileNotFoundError:
            print(f"Error: file '{self.filepath}' not found", file=sys.stderr)
            sys.exit(1)
        except ValueError as e:
            print(f"Config error: {e}", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            sys.exit(1)
        except OSError:
            print(f"Error: cannot read '{self.filepath}'", file=sys.stderr)
            sys.exit(1)

    def _validate_and_cast(self) -> None:
        """Check required keys, validate values and convert their types.

        Raises:
            ValueError: If a key is missing or a value is invalid.
        """

        missing_keys = self.REQUIRED_KEYS - set(self.config.keys())
        if missing_keys:
            raise ValueError(f"missing keys: {', '.join(missing_keys)}")

        width = self._to_int("WIDTH")
        height = self._to_int("HEIGHT")
        if width < 2 or height < 2:
            raise ValueError("WIDTH and HEIGHT must be at least 2")
        if width > 1000 or height > 1000:
            raise ValueError("WIDTH and HEIGHT must be at most 1000")
        self.config["WIDTH"] = width
        self.config["HEIGHT"] = height

        entry = self._to_coords("ENTRY", width, height)
        exit_ = self._to_coords("EXIT", width, height)
        if entry == exit_:
            raise ValueError("ENTRY and EXIT must be different")
        self.config["ENTRY"] = entry
        self.config["EXIT"] = exit_

        perfect_str = self.config["PERFECT"].lower()
        if perfect_str not in ("true", "false"):
            raise ValueError("PERFECT must be True or False")
        self.config["PERFECT"] = perfect_str == "true"

        if self.config["OUTPUT_FILE"] == "":
            raise ValueError("OUTPUT_FILE must not be empty")

        if "SEED" in self.config:
            self.config["SEED"] = self._to_int("SEED")

    def _to_int(self, key: str) -> int:
        """Convert the value of a key to an integer.

        Args:
            key: The configuration key to read.

        Returns:
            The value as an integer.

        Raises:
            ValueError: If the value is not a valid integer.
        """

        value = self.config[key]
        try:
            return int(value)
        except ValueError:
            raise ValueError(f"{key} must be an integer, got '{value}'")

    def _to_coords(self, key: str, width: int, height: int) -> tuple[int, int]:
        """Convert an "x,y" value to (x, y) and check it is inside the maze.

        Args:
            key: The configuration key to read, e.g. "ENTRY".
            width: Maze width, used to check x.
            height: Maze height, used to check y.

        Returns:
            The coordinates as an (x, y) tuple.

        Raises:
            ValueError: If the format is wrong or the cell is out of bounds.
        """

        value = self.config[key]
        parts = value.split(",")
        if len(parts) != 2:
            raise ValueError(f"{key} must look like x,y, got '{value}'")

        try:
            x = int(parts[0])
            y = int(parts[1])
        except ValueError:
            raise ValueError(f"{key} must be two integers, got '{value}'")

        if x < 0 or x >= width or y < 0 or y >= height:
            raise ValueError(f"{key} ({x},{y}) is outside the maze")
        return (x, y)
