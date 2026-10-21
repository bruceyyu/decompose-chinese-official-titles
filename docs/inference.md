# Local inference

## Prepare inputs

Use UTF-8 JSONL with one title per line, either a JSON string or an object:

```json
{"original_title": "知縣"}
```

Use the Qing adapter for Qing titles and the separate Korean-script adapter
for Joseon titles. The task determines the instruction, schema, and output
limit. The runtime checks the adapter's task metadata if present. It loads
the base-model revision recorded in the adapter configuration.

## Run

Install `pip install -e '.[inference]'`. Download the appropriate adapter
folder separately; the model cards describe the required files and licenses.

```bash
official-titles parse --task qing --adapter /path/to/qing-adapter \
  --input my-titles.jsonl --output private/parsed.jsonl --with-ranks
```

The first run may download the Qwen base model. Once both model and adapter
files are cached locally, paid inference services and API keys are not needed.
For disconnected use, cache the base model first and set `HF_HUB_OFFLINE=1`.
The optional `HF_TOKEN` follows the Hugging Face client's normal environment
handling; the package does not load or require an `.env` file.

Thinking is disabled and decoding is greedy, with 512 new tokens for Qing
and 256 for Joseon. Hardware, library versions, and inference engines can
still affect generated output. The runtime uses Transformers and PEFT rather
than merging the adapter into tied base-model weights. Sufficient memory is
required; CPU inference can be slow.
The default `--device-map auto` chooses the loading layout automatically.
Use `--device-map cpu`, `mps` (Apple Silicon), or `cuda:0` to request a device
explicitly when it is available and has sufficient memory.

Output must satisfy the exact task schema and retain `original_title`.
Invalid model records produce indexed error lines and a nonzero exit status;
no component is fabricated to repair a missing key. Malformed input JSON
stops the command. Completed preceding lines can remain in the new output
file. Existing files are never overwritten. Correct JSON is not proof of
historical correctness: validate the parser on new sources before relying on it.

## Validate or assign ranks without a model

```bash
official-titles validate --task qing \
  --input my-components.jsonl --output private/validated.jsonl
official-titles rank --input my-components.jsonl --output private/ranked.jsonl
```

These commands require the base package only. `rank` accepts complete Qing
schema records and adds separate numeric ranks and English labels. In Python,
`title_decomposition.rank_record` also accepts a partial component object:

```python
from title_decomposition import rank_record

result = rank_record({"duty_office": "知縣", "additional_title": ["五品銜"]})
# office_rank: 7 (7a); additional_title_rank: 5 (5a)
```

See [schema and rank definitions](schema.md) for missing/unranked values and
the retained-base-office rule. No Qing rank lookup is applied to Joseon output.
Training, held-out model evaluation, and career-mobility calculations are
outside this package's scope.
