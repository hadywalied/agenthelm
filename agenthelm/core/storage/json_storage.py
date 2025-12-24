import json
import os
from typing import Any, Dict, List
from .base import BaseStorage


class JsonStorage(BaseStorage):
    def __init__(self, file_path: str):
        self.file_path = file_path
        # Create the file with an empty list if it doesn't exist
        if not self.exists():
            with open(self.file_path, "w") as f:
                json.dump([], f)

    def save(self, data: Dict[str, Any], override=False) -> None:
        """
        Save data to a JSON file.
        If override is True, it will replace the entire file content.
        If override is False, it will append the data to the existing list.
        """
        if override:
            with open(self.file_path, "w") as f:
                json.dump([data], f, indent=2, default=str)
        else:
            current_data = self.load()
            current_data.append(data)
            with open(self.file_path, "w") as f:
                json.dump(current_data, f, indent=2, default=str)

    def load(self) -> List[Dict[str, Any]]:
        """Load data from a JSON file. Returns a list of dictionaries."""
        if not self.exists():
            return []
        with open(self.file_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []

    def exists(self) -> bool:
        """Check if the storage file exists."""
        return os.path.exists(self.file_path)
