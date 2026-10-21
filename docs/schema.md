# Output schema and rank definitions

`schemas/qing.json` specifies the output contract and `prompts/qing.txt` the
current training instruction. Both use `duty_office`, as do training targets,
parsed records, rank lookup, and field-level metrics. There is one public
schema per task; archived training formats are not part of this interface.

Single-valued component fields are strings or null:

- `duty_office`: normalized current post, stripped of status, honors, and location.
- `base_office`: substantive post retained during a deputation.
- `office_status`: acting, probationary, supernumerary, or other holding status.
- `qualification_title`: eligibility for an office not yet held.
- `jurisdiction`: territory or functional jurisdiction.
- `garrison`: stated place of station.
- `noble_title`: noble title, kept separate from the nine-rank office scale.

Multi-valued component fields are arrays of strings, empty when absent:

- `local_department`, `central_department`, `military_department`.
- `assignment`: concurrent, temporary, or specialized duties.
- `additional_title`: conferred office titles or grades without the post's duties.
- `ceremonial_office`, `warrior_title`, `honors_awards`.

`original_title` is a required, unchanged string and is excluded from the
fifteen-field average score. A missing key is invalid, even if its field could
otherwise be null. Schema validity and historical accuracy are different:
software validation does not establish a correct institutional reading.

The Joseon schema has `original_title`, `department`, and `position`. The latter
two are strings or null. Its prompt asks for only components printed in the
Korean-script title, not restoration of a normalized institutional hierarchy.

## Rank output

`rank_record` returns separate numeric `ranks` and English `rank_labels`.
The office rank records whether it came from the current or base office.
Following the paper's evaluation lookup, a ranked base office can stand in
when the current office has no rank from 1a through 9b. Raw current/base ranks
remain in the output: explicit unranked (10) is not an unmatched value (null).
The raw fields are `duty_office_rank` and `base_office_rank`; `office_rank`
is the selected rank after the base-office rule. Its source is recorded as
`duty_office` or `base_office`.
The rank-only API does not estimate mobility. The `title_ranks` lookup
consolidates institutional reference tables, not annotation labels. Its
reference table and documentation are included; noble and hereditary titles
are not mapped to office ranks. Multi-valued additional titles yield the most senior mapped rank
within that component; that does not combine additional titles with office rank.

