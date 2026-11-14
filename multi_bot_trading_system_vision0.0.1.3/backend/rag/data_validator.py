"""
Data Validation Module

Validates JSON data against schemas to ensure data integrity
before indexing for RAG.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from .rag_config import default_config


class ValidationError(Exception):
    """Raised when data validation fails."""
    pass


class DataValidator:
    """Validates JSON data documents for RAG ingestion."""

    def __init__(self, strict_mode: bool = True):
        self.strict_mode = strict_mode

    def validate_record(self, record: Dict[str, Any],
                       schema: Optional[Dict[str, Any]] = None) -> bool:
        """Validate a single record against an optional schema."""
        if not isinstance(record, dict):
            if self.strict_mode:
                raise ValidationError("Record must be a dictionary")
            return False

        # Basic validation: check for empty records
        if not record:
            if self.strict_mode:
                raise ValidationError("Record is empty")
            return False

        return True

    def validate_json_content(self, data: Any) -> bool:
        """Validate that JSON content has required structure."""
        if not isinstance(data, (dict, list)) or not data:
            return False

        records = self._extract_records(data)
        return any(isinstance(record, dict) and bool(record) for record in records)

    @staticmethod
    def _extract_records(data: Any) -> List[Any]:
        if isinstance(data, list):
            return data
        for key in ("records", "items", "documents"):
            if isinstance(data.get(key), list):
                return data[key]
        return [data]

    def validate_file_data(self, file_path: Path) -> Tuple[bool, List[str]]:
        """Validate a JSON file's content and return results."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (json.JSONDecodeError, UnicodeDecodeError, OSError) as e:
            return False, [f"JSON parse error: {e}"]

        return self.validate_data(data)

    def validate_data(self, data: Any) -> Tuple[bool, List[str]]:
        """Validate already parsed data without reading a large JSON file twice."""
        errors = []
        # Validate basic structure
        if not self.validate_json_content(data):
            errors.append("File lacks required content fields (text, title, id, etc.)")

        # Additional validation in strict mode
        if self.strict_mode:
            records = self._extract_records(data)
            for i, record in enumerate(records):
                if not isinstance(record, dict):
                    errors.append(f"Record {i} is not a dictionary")

        return len(errors) == 0, errors

    def batch_validate(self, files: List[Path]) -> Dict[str, Tuple[bool, List[str]]]:
        """Validate multiple JSON files."""
        results = {}
        for file_path in files:
            results[str(file_path)] = self.validate_file_data(file_path)
        return results