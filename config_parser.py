"""Read and validate the configuration file of the maze generator."""

from typing import Any


class ConfigError(ValueError):
    """Raised when the configuration file cannot be used."""


class ConfigParser:
    """Parse and validate the configuration file of the maze generator."""

    REQUIRED_KEYS = frozenset(
        {"WIDTH", "HEIGHT", "ENTRY", "EXIT", "OUTPUT_FILE", "PERFECT"}
    )
    OPTIONAL_KEYS = frozenset({"SEED"})
    MIN_SIZE = 2
    MAX_SIZE = 1000

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

        Raises:
            ConfigError: If the file cannot be read or a value is invalid.
        """
        self.config = {}
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                lines = f.read().splitlines()
        except FileNotFoundError:
            raise ConfigError(f"file '{self.filepath}' not found") from None
        except UnicodeDecodeError:
            raise ConfigError(
                f"'{self.filepath}' is not a valid text file"
            ) from None
        except OSError as e:
            raise ConfigError(
                f"cannot read '{self.filepath}': {e.strerror}"
            ) from None

        for number, raw_line in enumerate(lines, start=1):
            self._read_line(number, raw_line)
        self._validate_and_cast()
        return self.config

    def _read_line(self, number: int, raw_line: str) -> None:
        """Store the KEY=VALUE pair of one line, ignoring comments."""
        line = raw_line.strip()
        if not line or line.startswith("#"):
            return

        if "=" not in line:
            raise ConfigError(f"line {number}: missing '=' in '{line}'")

        key, value = line.split("=", 1)
        key = key.strip().upper()
        value = value.strip()

        if key == "":
            raise ConfigError(f"line {number}: empty key in '{line}'")
        if key not in self.REQUIRED_KEYS | self.OPTIONAL_KEYS:
            raise ConfigError(f"line {number}: unknown key '{key}'")
        if key in self.config:
            raise ConfigError(f"line {number}: duplicate key '{key}'")

        self.config[key] = value

    def _validate_and_cast(self) -> None:
        """Check required keys, validate values and convert their types.

        Raises:
            ConfigError: If a key is missing or a value is invalid.
        """
        missing_keys = self.REQUIRED_KEYS - set(self.config)
        if missing_keys:
            missing = ", ".join(sorted(missing_keys))
            raise ConfigError(f"missing keys: {missing}")

        width = self._to_int("WIDTH")
        height = self._to_int("HEIGHT")
        if width < self.MIN_SIZE or height < self.MIN_SIZE:
            raise ConfigError(
                f"WIDTH and HEIGHT must be at least {self.MIN_SIZE}"
            )
        if width > self.MAX_SIZE or height > self.MAX_SIZE:
            raise ConfigError(
                f"WIDTH and HEIGHT must be at most {self.MAX_SIZE}"
            )
        self.config["WIDTH"] = width
        self.config["HEIGHT"] = height

        entry = self._to_coords("ENTRY", width, height)
        exit_ = self._to_coords("EXIT", width, height)
        if entry == exit_:
            raise ConfigError("ENTRY and EXIT must be different")
        self.config["ENTRY"] = entry
        self.config["EXIT"] = exit_

        perfect = self.config["PERFECT"].lower()
        if perfect not in ("true", "false"):
            raise ConfigError("PERFECT must be True or False")
        self.config["PERFECT"] = perfect == "true"

        if self.config["OUTPUT_FILE"] == "":
            raise ConfigError("OUTPUT_FILE must not be empty")

        if "SEED" in self.config:
            self.config["SEED"] = self._to_int("SEED")

    def _to_int(self, key: str) -> int:
        """Convert the value of a key to an integer.

        Raises:
            ConfigError: If the value is not a valid integer.
        """
        value = self.config[key]
        try:
            return int(value)
        except ValueError:
            raise ConfigError(
                f"{key} must be an integer, got '{value}'"
            ) from None

    def _to_coords(self, key: str, width: int, height: int) -> tuple[int, int]:
        """Convert an "x,y" value to (x, y) and check it is inside the maze.

        Raises:
            ConfigError: If the format is wrong or the cell is out of bounds.
        """
        value = self.config[key]
        parts = value.split(",")
        if len(parts) != 2:
            raise ConfigError(f"{key} must look like x,y, got '{value}'")

        try:
            x = int(parts[0])
            y = int(parts[1])
        except ValueError:
            raise ConfigError(
                f"{key} must be two integers, got '{value}'"
            ) from None

        if x < 0 or x >= width or y < 0 or y >= height:
            raise ConfigError(f"{key} ({x},{y}) is outside the maze")
        return (x, y)
