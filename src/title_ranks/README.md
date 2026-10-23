# Qing component-rank lookup

`title_ranks` assigns ranks after a compound title has been decomposed.
It combines an institutional lookup table with context-sensitive rules.
The `title_decomposition.rank_record` wrapper keeps the ranks of
offices, additional titles, and eligibility separate.

## Historical scope

The mappings reflect our interpretation of **late-Qing ranks**, drawing mainly
on the Guangxu Huidian, and may contain errors. The same office title may have
a different rank in the early Qing, Ming, or another bureaucratic system.
Check the mappings against the period and institutions you study, and revise
or replace them where needed.

## Interfaces and scale

```python
from title_ranks import office_rank, component_rank

rank = office_rank("郎中", departments=["戶部"], full_title="戶部郎中")  # 5.0
additional_rank = component_rank(["五品銜"])  # 5.0
```

Both functions above use lower = more senior: 1a = 1, 1b = 1.5, through
9b = 9.5. Explicitly unranked is 10; unknown or absent is `None`. Do not replace
unknown values with 10. A multi-valued component returns its most senior mapped
rank, not a rank collapsed across institutionally different components.

## Tables and resolution

[`data/office_ranks.csv`](data/office_ranks.csv) consolidates the compiled
Guangxu Huidian office-rank list and supplementary office mappings, spelling
variants, and corrections. Each office has one row: `office`,
`canonical_office`, numeric `rank`, English `rank_label`, `source`, and `note`.
Editorial group headings are expanded into individual forms. These are
institutional mappings, not annotations of individual compound titles or
person-level records. The resolver uses the same rank scale throughout and
requires only the Python standard library.

Resolution recognizes explicit grades in the office wording, more specific
forms in the full title, department-qualified offices, exact matches, and
eligible suffix matches. It does not indiscriminately search for every office
substring within a longer title. Noble and hereditary titles are excluded
from the table; the parser can still return them in `noble_title`.

Bare or prefixed 筆帖式 has a register-compatible fallback of 10
unless the wording gives an adjacent substantive grade. This is a documented
database convention, **not** a claim that every historical holder was unranked.
A grade modifying an additional title does not become the substantive office's
grade: in 六品銜筆帖式, 六品銜 is not the office grade. Other unresolved offices
remain unknown. Full-title and department context can therefore matter even
after decomposition. This convention can be changed in `office_rank` if a
different source warrants it.

## Use your own mappings

To use a separate rank table, parse titles without `--with-ranks`, then match
the components against your table. For a single-period CSV with columns
`office` and `rank`, using one row per office:

```python
import csv

with open("my_office_ranks.csv", encoding="utf-8", newline="") as stream:
    ranks = {row["office"]: float(row["rank"]) for row in csv.DictReader(stream)}

# record is a decomposed title; an unmatched office returns None.
rank = ranks.get(record["duty_office"])
```

Use the same numeric scale as above. Include department and year in matching
keys where ranks depend on context, and keep source notes with your mappings.
Match base offices, additional titles, and eligibility separately.

To modify the bundled lookup instead, edit `data/office_ranks.csv` in your
local checkout, keeping office keys unique and updating `canonical_office`,
`rank_label`, `source`, and `note`. Restart Python or the notebook kernel to
reload it. Explicit-grade
and context rules in [`__init__.py`](__init__.py) can take precedence over table
entries; review those rules when adapting the resolver.
