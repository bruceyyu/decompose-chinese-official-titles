"""Artificial fixture, not a row from the authors' annotation collection."""
import json

from title_decomposition import rank_record

# A user-supplied decomposition can be ranked without loading any language model.
# This artificial combination illustrates why component ranks stay separate.
record = {
    "original_title": "知縣加五品銜",
    "duty_office": "知縣",
    "additional_title": ["五品銜"],
}
print(json.dumps(rank_record(record), ensure_ascii=False, indent=2))
