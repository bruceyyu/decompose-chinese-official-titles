# Local inference

## Prepare inputs

Use UTF-8 JSONL, with one title per line as a JSON string or an object:

```json
{"original_title": "知縣"}
```

## Parse titles

```bash
python -m pip install -e '.[inference]'
official-titles parse --task qing --adapter bruceyyu/qing-title-decomposition \
  --input my-titles.jsonl --output private/parsed.jsonl --with-ranks
```

For Joseon titles, use `--task joseon` and
`--adapter bruceyyu/joseon-title-decomposition`, omitting `--with-ranks`.
A local adapter folder can replace either repository ID.

The first run downloads the adapter and its configured Qwen base-model
revision. Inference uses Transformers and PEFT, greedy decoding, and disabled
thinking. Output limits are 512 new tokens for Qing and 256 for Joseon.

`--device-map auto` selects the loading layout. Use `cpu`, `mps` (Apple Silicon),
or `cuda:0` to select a device. A GPU is recommended; CPU inference is slower.
For offline use, cache the models first and set `HF_HUB_OFFLINE=1`.
Use `HF_TOKEN` when accessing a private model repository.

Each response is checked against the task schema and must preserve
`original_title`. Failed records produce indexed error entries and a nonzero
exit status. Malformed input JSON stops processing; preceding output remains.
Choose a new output filename for each run.

## Validate components or assign ranks

```bash
official-titles validate --task qing \
  --input my-components.jsonl --output private/validated.jsonl
official-titles rank --input my-components.jsonl --output private/ranked.jsonl
```

These commands use the base installation, `python -m pip install -e .`.
The CLI expects complete component records. The Python rank function also
accepts partial records:

```python
from title_decomposition import rank_record

result = rank_record({"duty_office": "知縣", "additional_title": ["五品銜"]})
# office_rank: 7 (7a); additional_title_rank: 5 (5a)
```

See [schema and rank definitions](schema.md) and the
[public-data mobility example](public_mobility.md).
