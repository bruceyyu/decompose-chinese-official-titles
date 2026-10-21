"""One output contract: duty_office in prompts, schemas, training and results."""
from __future__ import annotations

from typing import Any

from ._qing_protocol import ARRAY_FIELDS, STRING_FIELDS


class SchemaError(ValueError):
    """A model response is not a valid decomposition of the supplied title."""


def validate_record(value: Any, task: str = "qing", original_title: str | None = None) -> dict:
    if not isinstance(value, dict):
        raise SchemaError("Expected one JSON object")
    record = dict(value)
    if task == "qing":
        strings = STRING_FIELDS
        arrays = ARRAY_FIELDS
    elif task == "joseon":
        strings, arrays = ["original_title", "department", "position"], []
    else:
        raise ValueError(f"Unknown task: {task}")
    expected = set(strings) | set(arrays)
    if set(record) != expected:
        missing, extra = sorted(expected - set(record)), sorted(set(record) - expected)
        raise SchemaError(f"Schema keys differ: missing={missing}; extra={extra}")
    if not isinstance(record["original_title"], str):
        raise SchemaError("original_title must be a string")
    if original_title is not None and record["original_title"] != original_title:
        raise SchemaError("The response changed original_title")
    for key in strings:
        if record[key] is not None and not isinstance(record[key], str):
            raise SchemaError(f"{key} must be a string or null")
    for key in arrays:
        if not isinstance(record[key], list) or not all(isinstance(item, str) for item in record[key]):
            raise SchemaError(f"{key} must be an array of strings")
    return record


def json_schema(task: str = "qing") -> dict:
    if task == "qing":
        strings = STRING_FIELDS
        arrays = ARRAY_FIELDS
    elif task == "joseon":
        strings, arrays = ["original_title", "department", "position"], []
    else:
        raise ValueError(f"Unknown task: {task}")
    properties = {key: {"type": "string" if key == "original_title" else ["string", "null"]}
                  for key in strings}
    properties.update({key: {"type": "array", "items": {"type": "string"}} for key in arrays})
    return {"$schema": "https://json-schema.org/draft/2020-12/schema", "type": "object",
            "additionalProperties": False, "properties": properties, "required": list(properties)}

