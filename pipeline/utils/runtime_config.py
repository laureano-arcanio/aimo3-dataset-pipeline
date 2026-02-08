"""Hot-reloadable JSON config that can be edited while a run is in progress."""

from __future__ import annotations

import json
from pathlib import Path


class RuntimeConfig:
    """Read settings from a JSON file; call ``reload()`` to pick up edits.

    Parameters
    ----------
    path : str | Path
        Path to the JSON config file.
    defaults : dict
        Default values for every recognised key.  Keys not listed here
        are ignored when reading the file.
    """

    def __init__(self, path: str | Path, defaults: dict):
        self.path = Path(path)
        self._fields = tuple(defaults)
        for k, v in defaults.items():
            setattr(self, k, v)
        if self.path.exists():
            self.reload()
        self.save()

    def reload(self) -> list[str]:
        """Re-read the JSON file.  Returns a list of ``"KEY: old -> new"`` strings."""
        changed: list[str] = []
        try:
            data = json.loads(self.path.read_text())
            for key in self._fields:
                if key in data:
                    old = getattr(self, key)
                    new_val = data[key]
                    if old != new_val:
                        setattr(self, key, new_val)
                        changed.append(f"{key}: {old} -> {new_val}")
            if changed:
                log_msg = f"Config reloaded: {', '.join(changed)}"
                print(log_msg)
        except Exception as e:
            error_msg = f"Config reload error: {e}"
            print(error_msg)
        return changed

    def save(self) -> None:
        """Write current values back to the JSON file."""
        data = {k: getattr(self, k) for k in self._fields}
        self.path.write_text(json.dumps(data, indent=2) + "\n")

    def __repr__(self) -> str:
        items = ", ".join(f"{k}={getattr(self, k)!r}" for k in self._fields)
        return f"RuntimeConfig({items})"
