"""Settings for pywam gui application."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NamedTuple

SETTINGS_FILE = Path(__file__).parent.joinpath("settings.json")
DEFAULT_SETTINGS = {
    "hosts": [{"name": "Speaker", "host": "192.168.1.100", "port": 55001}],
    "loglevel": 1,
    "default_host": 0,
}


class Host(NamedTuple):
    """Speaker host information."""

    name: str
    host: str
    port: int


class Settings:
    """Application settings."""

    def __init__(self) -> None:
        """Initialize settings."""
        self._settings: dict = {}

    def load_settings(self) -> None:
        """Load settings."""
        try:
            with open(SETTINGS_FILE) as f:
                self._settings = json.load(f)
        except FileNotFoundError:
            self._settings = DEFAULT_SETTINGS
        except Exception as err:
            self._settings = {"ERROR": str(err)}

    def save_settings(self) -> None:
        """Save settings."""
        with open(SETTINGS_FILE, "w") as f:
            json.dump(self._settings, f, sort_keys=True, indent=4)

    @property
    def error(self) -> str | None:
        """Return error message."""
        return self._settings.get("ERROR")

    @property
    def hosts(self) -> list[Host]:
        """Return list of hosts."""
        return [Host(**host) for host in self._settings.get("hosts", [])]

    @hosts.setter
    def hosts(self, hosts: list[Host]) -> None:
        """Set list of hosts."""
        self._settings["hosts"] = [host._asdict for host in hosts]
        self.save_settings()

    @property
    def default_host(self) -> int:
        """Return default host."""
        return self._settings.get("default_host", 0)

    @default_host.setter
    def default_host(self, default_host: int) -> None:
        """Set default host."""
        if not isinstance(default_host, int):
            raise TypeError("Default host must be an integer")
        if default_host < 0 or default_host >= len(self.hosts):
            raise ValueError("Default host must be one of the hosts")
        self._settings["default_host"] = default_host
        self.save_settings()

    @property
    def loglevel(self) -> int:
        """Return level of logging."""
        return self._settings.get("loglevel", 1)

    @loglevel.setter
    def loglevel(self, loglevel: int) -> None:
        """Set level of logging."""
        if not isinstance(loglevel, int):
            raise TypeError("loglevel must be an integer")
        if not -1 < loglevel < 5:
            raise ValueError("loglevel must be between 0 and 4")
        self._settings["loglevel"] = loglevel
        self.save_settings()
