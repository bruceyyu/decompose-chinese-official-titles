# Office, Rank, and Mobility: Decomposing Historical Chinese Bureaucratic Titles with Language Models

[![Preprint: SocArXiv](https://img.shields.io/badge/Preprint-SocArXiv-2C7FB8)](https://osf.io/preprints/socarxiv/eg87f_v1)
[![Qing model](https://img.shields.io/badge/Hugging%20Face-Qing%20model-FFD21E?logo=huggingface)](https://huggingface.co/bruceyyu/qing-title-decomposition)
[![Parsed CGED-Q JSL data](https://img.shields.io/badge/Data-CGED--Q%20JSL-4C9F38)](https://dataverse.harvard.edu/file.xhtml?fileId=14356735&version=12.0)
[![Code license: PolyForm Noncommercial](https://img.shields.io/badge/Code%20license-PolyForm%20NC-blue)](LICENSE)

This repository contains the inference code for [*Office, Rank, and Mobility:
Decomposing Historical Chinese Bureaucratic Titles with Language Models*](https://osf.io/preprints/socarxiv/eg87f_v1),
by Yue Yu, Jun Chen, Michael Y. H. Chung, and Cameron Campbell. The method
separates the institutional components of historical bureaucratic titles before
converting them into measures of office and rank.

## Overview

A compound title can describe an official's current post, additional titles,
and eligibility for offices not yet held. These do not necessarily have the
same rank. For example, 知縣加五品銜 combines a county magistrate's post
(rank 7a) with an additional title of rank 5a.

The code supports three tasks:

1. Decompose Qing titles into fifteen components, including the duty office,
   additional titles, qualifications, departments, and assignments.
2. Assign separate Qing ranks to offices, additional titles, and qualifications
   using an institutional lookup table.
3. Decompose Korean-script Joseon titles into department and post using a
   separately adapted model.

The models identify components; numeric ranks are assigned afterward.
The Qing and Joseon adapters use different schemas and are not interchangeable.

## Table of Contents

- [Installation](#installation)
- [Models and Data](#models-and-data)
- [Workflow](#workflow)
- [Step-by-Step Instructions](#step-by-step-instructions)
- [Interactive Demo](#interactive-demo)
- [Output and Rank Definitions](#output-and-rank-definitions)
- [Repository Structure](#repository-structure)
- [Citation](#citation)
- [License](#license)

## Installation

Use Python 3.11 or newer. From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[inference]'
```

This installs the `official-titles` command and the local inference dependencies.
For rank lookup and output validation without a model, install only the base
package with `python -m pip install -e .`.

Local inference requires enough memory for the base model and adapter.
A GPU is recommended; CPU inference can be slow.

## Models and Data

### Models

Both tasks use a LoRA adapter on top of
[Qwen/Qwen3.5-4B](https://huggingface.co/Qwen/Qwen3.5-4B):

- **[Qing adapter](https://huggingface.co/bruceyyu/qing-title-decomposition):** fifteen-component decomposition. See the [model card](model_cards/qing.md).
- **[Joseon adapter](https://huggingface.co/bruceyyu/joseon-title-decomposition):** department and post in Korean-script titles. See the [model card](model_cards/joseon.md).

Supply the adapter's local folder or Hugging Face repository ID through
`--adapter`. The runtime obtains the base model separately, using the revision
recorded in the adapter configuration. The first run may download model files;
cached models run locally without a paid inference API.

### Input data

Provide titles as UTF-8 JSONL, with one title per line. The files in
[examples/](examples/) contain artificial teaching examples, not records from
the annotation collection.

### Public parsed titles

Model-parsed titles from the public CGED-Q Jinshenlu records are available
on [Harvard Dataverse](https://dataverse.harvard.edu/file.xhtml?fileId=14356735&version=12.0).
These are model-generated decompositions, not the human-annotated training
or evaluation data.

The underlying public CGED-Q records are available through the
[CGED-Q dataset](https://doi.org/10.7910/DVN/GMQWVZ), subject to its access
conditions. The data are hosted separately; this code repository does not include
CGED-Q records or human annotations.

## Workflow

```text
Title strings (JSONL)
    ↓
Qing or Joseon adapter
    ↓
Validated institutional components (JSONL)
    ↓  optional, Qing only
Separate office, additional-title, and eligibility ranks
```

Output validation is part of inference: responses must have the required
fields and preserve the original title. Rank lookup can also be applied to
components supplied by the user, without loading a language model.

## Step-by-Step Instructions

### Step 1: Prepare titles

Each line may be a JSON string or an object containing `original_title`:

```json
{"original_title": "知縣"}
{"original_title": "戶部郎中"}
```

Use [examples/titles.jsonl](examples/titles.jsonl) to try Qing parsing and
[examples/korean-titles.jsonl](examples/korean-titles.jsonl) for Joseon.

### Step 2: Decompose titles

The commands below use the Hugging Face adapters. A downloaded local folder
can be supplied instead. Access to a private repository requires Hugging Face
authentication, for example through `hf auth login`.

For Qing titles:

```bash
official-titles parse --task qing --adapter bruceyyu/qing-title-decomposition \
  --input examples/titles.jsonl --output private/qing-components.jsonl
```

For Korean-script Joseon titles:

```bash
official-titles parse --task joseon --adapter bruceyyu/joseon-title-decomposition \
  --input examples/korean-titles.jsonl --output private/joseon-components.jsonl
```

Key options and settings:

- `--task`: selects the task's prompt and output schema.
- `--adapter`: selects the matching local adapter or Hugging Face repository.
- `--device-map`: defaults to `auto`; use `cpu`, `mps` (Apple Silicon),
  or `cuda:0` to request an available device.
- Thinking is disabled and decoding is greedy, with up to 512 new tokens
  for Qing and 256 for Joseon.

### Step 3: Assign Qing ranks (optional)

Apply the lookup to the complete component records from Step 2:

```bash
official-titles rank --input private/qing-components.jsonl \
  --output private/qing-ranked.jsonl
```

Alternatively, add `--with-ranks` to the Qing `parse` command to decompose and
rank in one step. The Qing lookup must not be applied to Joseon titles.

To try rank lookup without a model:

```bash
python examples/rank_only.py
```

The Python interface also accepts partial component records:

```python
from title_decomposition import rank_record

result = rank_record({
    "original_title": "知縣加五品銜",
    "duty_office": "知縣",
    "additional_title": ["五品銜"],
})
# result["rank_labels"]["office_rank"] == "7a"
# result["rank_labels"]["additional_title_rank"] == "5a"
```

## Interactive Demo

Install the optional Gradio interface and start the Qing demo:

```bash
python -m pip install -e '.[inference,demo]'
official-titles-demo --task qing
```

Open `http://127.0.0.1:7860`. Enter a title or select an illustrative example,
then click **Decompose title**. The page shows the complete component record
and separate Qing rank results. It loads the published
Hugging Face adapter, not precomputed answers. The first request loads the
model; later requests reuse it.

Use `--device-map mps` for Apple Silicon or `--device-map cuda:0` for an
available CUDA GPU. To use the other task, restart with `--task joseon`;
only one model is loaded per app. `--adapter` can override the default Hub ID.
The demo listens on localhost and does not create a public sharing link.
It does not save entered titles or predictions to a dataset.

## Output and Rank Definitions

Each output line is a JSON object.

- **Qing:** the unchanged `original_title` and fifteen components.
  Single-valued components are strings or `null`; multi-valued components
  are arrays, empty when absent.
- **Joseon:** `original_title`, `department`, and `position`.
- **Qing with ranks:** adds `ranks`, `rank_labels`, and `office_rank_source`.

Numeric ranks are lower for more senior grades: `1a = 1`, `1b = 1.5`, through
`9b = 9.5`. The value `10` means explicitly unranked; `null` means absent or
unmatched. Duty-office, retained-base-office, additional-title, and eligibility
ranks remain separate. When the current post has no rank on the nine-rank
scale, a ranked retained base office can supply `office_rank`; its source
is recorded. Noble and hereditary titles are not assigned office ranks.

Output paths must be new files; existing files are never overwritten.
Invalid model responses produce indexed error records and a nonzero exit
status. Correct JSON does not establish historical accuracy: inspect results
and validate the method when applying it to a new source.

See [schema and rank definitions](docs/schema.md),
[rank lookup documentation](src/title_ranks/README.md), and
[inference notes](docs/inference.md) for details.

## Repository Structure

```text
src/title_decomposition/   # Inference, command-line interface, and output validation
src/title_ranks/           # Qing rank resolver and consolidated reference table
prompts/                  # Task-specific model instructions
schemas/                  # JSON output schemas
configs/                  # Training configurations
model_cards/              # Model descriptions, evaluations, and limitations
examples/                 # Artificial input and rank-lookup examples
docs/                     # Inference, schema, and licensing documentation
```

Adapter weights are distributed separately on Hugging Face, not in this
code repository.

## Citation

If you use this code or the methodology introduced in our paper, please cite:

```bibtex
@misc{yu_chen_chung_campbell_2026,
  title={Office, Rank, and Mobility: Decomposing Historical Chinese Bureaucratic Titles with Language Models},
  url={https://osf.io/preprints/socarxiv/eg87f_v1},
  publisher={SocArXiv},
  author={Yu, Yue and Chen, Jun and Chung, Michael Y H and Campbell, Cameron},
  year={2026},
  month={Oct}
}
```

## License

Code is distributed under [PolyForm Noncommercial 1.0.0](LICENSE).
Retain the attribution in [NOTICE](NOTICE).
The authors' adapter contributions, prompts, documentation, and original
lookup-table compilation use [CC BY-NC 4.0](licenses/CC-BY-NC-4.0.txt).
The base model and third-party materials retain their own licenses.
See [licensing notes](docs/licensing.md).

## Contact

Please refer to the manuscript for contact details.
