"""Decompose official titles without conflating their institutional components."""
from .schema import SchemaError, validate_record
from .ranks import rank_record

__all__ = ["SchemaError", "validate_record", "rank_record"]
__version__ = "0.2.0"

