# Output schema and ranks

## Qing components

The [Qing schema](../schemas/qing.json) contains `original_title` and fifteen
components. All fields are required; `original_title` preserves the input.

Single-valued fields are strings, or `null` when absent:

- `duty_office`: normalized current post.
- `base_office`: substantive post retained during a deputation.
- `office_status`: acting, probationary, supernumerary, or other status.
- `qualification_title`: eligibility for an office not yet held.
- `jurisdiction`: territorial or functional jurisdiction.
- `garrison`: place of station.
- `noble_title`: noble title.

Multi-valued fields are arrays of strings, empty when absent:

- `local_department`, `central_department`, `military_department`.
- `assignment`: concurrent, temporary, or specialized duties.
- `additional_title`: office titles or grades held without the post's duties.
- `ceremonial_office`, `warrior_title`, `honors_awards`.

## Joseon components

The [Joseon schema](../schemas/joseon.json) contains `original_title`,
`department`, and `position`. The latter two are strings or `null`, identifying
components printed in the Korean-script title.

## Qing ranks

Rank output has three entries: `ranks`, `rank_labels`, and `office_rank_source`.
The numeric scale runs from **1a = 1** to **9b = 9.5**, in half-point steps;
lower values mean greater seniority. **10** means explicitly unranked;
**null** means absent or unmatched. English labels use `1a`, `1b`, and so on.

The `ranks` fields are:

- `duty_office_rank` and `base_office_rank`: separate office ranks.
- `office_rank`: duty-office rank, using a ranked base office when the duty
  office is unranked or unmatched.
- `additional_title_rank`: the most senior mapped additional title.
- `eligibility_rank`: the rank of the office for which the official is eligible.

`office_rank_source` identifies `duty_office` or `base_office`, or is `null`
when the selected office rank is unavailable. Noble and hereditary titles
remain separate from office ranks. Rank lookup applies to Qing components.

The public CGED-Q tables name the eligibility-rank column
`qualification_title_rank`. See the [lookup documentation](../src/title_ranks/README.md)
for institutional sources, historical scope, and custom mappings.

