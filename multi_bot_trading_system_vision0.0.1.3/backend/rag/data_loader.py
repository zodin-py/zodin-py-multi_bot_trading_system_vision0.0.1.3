"""
Data Loading Module

Reads JSON files and prepares them for RAG processing.
Handles loading JSON knowledge base files from the data directory.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Any, Optional
from .rag_config import default_config


class DataLoader:
    """Loads and validates JSON data files for RAG ingestion."""

    def __init__(self, data_dir: Optional[Path] = None, json_dir: Optional[Path] = None):
        self.data_dir = data_dir or default_config.data_dir
        self.json_dir = json_dir or default_config.json_files_dir
        self._file_hashes: Dict[str, str] = {}
        self.load_errors: List[str] = []

    def discover_json_files(self) -> List[Path]:
        """Discover all JSON files in the data directory."""
        if not self.json_dir.exists():
            return []
        return sorted(self.json_dir.glob("*.json"))

    def compute_file_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of a file for change detection."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()

    def load_json_file(self, file_path: Path) -> Optional[Any]:
        """Load and parse a single JSON file with validation."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            if data is None:
                self.load_errors.append(file_path.name)
                return None
            return data
        except (json.JSONDecodeError, UnicodeDecodeError, OSError):
            self.load_errors.append(file_path.name)
            return None

    def load_all_json_files(self) -> Dict[str, Any]:
        """Load all JSON files and return a filename-to-data mapping."""
        files = self.discover_json_files()
        results = {}
        self.load_errors = []
        self._file_hashes = {}
        for file_path in files:
            data = self.load_json_file(file_path)
            if data is not None:
                results[file_path.name] = data
                self._file_hashes[file_path.name] = self.compute_file_hash(file_path)
        return results

    def compute_current_hashes(self) -> Dict[str, str]:
        """Hash source files without parsing them, for inexpensive change checks."""
        self.load_errors = []
        hashes = {}
        for file_path in self.discover_json_files():
            try:
                hashes[file_path.name] = self.compute_file_hash(file_path)
            except OSError:
                self.load_errors.append(file_path.name)
        return hashes

    def detect_changes(self, current_hashes: Dict[str, str]) -> Dict[str, List[str]]:
        """Detect which files have changed, been added, or removed."""
        changes = {
            "modified": [],
            "added": [],
            "removed": []
        }

        current_keys = set(current_hashes.keys())
        stored_keys = set(self._file_hashes.keys())

        # Modified files
        for key in current_keys & stored_keys:
            if current_hashes[key] != self._file_hashes[key]:
                changes["modified"].append(key)

        # Added files
        for key in current_keys - stored_keys:
            changes["added"].append(key)

        # Removed files
        for key in stored_keys - current_keys:
            changes["removed"].append(key)

        return changes

    def get_cached_hashes(self) -> Dict[str, str]:
        """Return cached file hashes."""
        return self._file_hashes.copy()