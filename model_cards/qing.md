---
base_model: Qwen/Qwen3.5-4B
library_name: peft
license: cc-by-nc-4.0
language:
  - zh
tags:
  - historical-text
  - information-extraction
  - lora
  - qing
---

# Qing official-title decomposition adapter

A LoRA adapter for **Qwen/Qwen3.5-4B**, not a standalone model. It separates
compound Qing bureaucratic titles into fifteen institutional components.
The accompanying code converts components to ranks separately; the model
does not predict numeric ranks or career mobility.

Related manuscript: *Office, Rank, and Mobility: Decomposing Historical Chinese
Bureaucratic Titles with Language Models*, Yue Yu, Jun Chen, Michael Yan Hon
Chung, and Cameron Campbell.

Preprint: https://osf.io/preprints/socarxiv/eg87f_v1

Code: https://github.com/bruceyyu/decompose-chinese-official-titles

## Use

Install the codebase with `pip install -e '.[inference]'`, then:

```bash
official-titles parse --task qing --adapter /path/to/adapter \
  --input my-titles.jsonl --output my-components.jsonl --with-ranks
```

Each input is a JSON string or an object with `original_title`. The exact
instruction is in `prompt.txt`. Disable thinking, decode greedily, and allow
up to 512 new tokens. `duty_office` is the office field throughout the schema,
instruction, and interface. Single-valued components are strings or null;
multi-valued components are arrays, empty when absent. Output must retain
`original_title` unchanged.

## Adaptation and selection

The release model is a new training run dated 2026-10-21, not a recovered copy
of the historical benchmark checkpoint. The adaptation pool contains 1,967
distinct annotated titles: 1,770 for optimization and 197 for internal
validation. Two external holdouts each contain 200 titles and are excluded
from optimization and checkpoint selection.

The recipe uses rank-64 LoRA, learning rate 2e-4 with linear decay over a
six-epoch horizon, four completed epochs, batch size 32, sequence limit 3,000,
and shuffle seed 42. Loss applies only to the assistant response and is
normalized per example. Selection minimizes internal validation negative
log-likelihood at completed epochs. Training configuration is provided;
training scripts and reference annotations are not distributed.

Internal validation selected epoch 2, step 110 (NLL 0.025720). This is a new
checkpoint from the retraining run, not the unavailable historical checkpoint
with the same step number. The selected weights are backed up locally.

## Evaluation boundaries

On the two 200-title holdouts, the retrained release model scores **94.02%**
(fixed) and **93.38%** (rare-component-stratified), averaging exact agreement
for strings and set F1 for arrays across fifteen components. Whole-record
exact agreement is 48.0% and 49.0%, respectively. Both sets have 100% schema
validity. The input title is reproduced exactly in 99.5% and 100% of cases;
the local parser rejects a response that changes the input title.

These new evaluations use the original training runtime, not a full rerun in
the exported PEFT runtime. They differ slightly from the manuscript's
historical checkpoint results. The weights and scores must not be presented
as an exact recovery of that earlier experiment.

Empty fields contribute to the average, and rare fields have small support.
Current-office exact agreement is 84.0% and 82.5%; assignment set F1 is 78.04%
and 75.89%. The field average must not be read as uniformly high accuracy or
as the share of complete titles parsed correctly. The fixed holdout is not a random
population sample; the stratified holdout deliberately includes rare fields.
Annotation is primarily by one annotator rather than independent expert panels.
Withheld labels prevent independent reproduction of the original accuracy
benchmark from this package alone.

The newly trained adapter must not be assumed to have generated the
manuscript's earlier decomposed career dataset. Exported-runtime accuracy and
structural/matrix checks are different forms of verification. A two-example
local generation smoke test has also passed; it is not an accuracy benchmark.
Consult `verification.json` for what has actually been tested.

## Scope and limitations

Intended for research on historical bureaucratic titles, especially Jinshenlu.
The parser can normalize institutional wording rather than only copy spans.
Valid JSON or a recognized rank does not establish a correct institutional
reading. Unfamiliar sources, OCR errors, different periods, and new organizations
require validation. Additional titles, eligibility, and actual posts are not
interchangeable. Do not use the model for consequential decisions about living
individuals.

The compatible PEFT export preserves separate adapter contributions to the
output head. Do not merge it into tied base weights without validating the
merged runtime. Base-model weights are obtained separately.

## Files and licensing

The model folder contains adapter weights and configuration, this card, prompt,
schema, checksums, and verification information. It contains no base weights,
credentials, human annotation rows, or person-level records. The authors'
adapter contributions and model materials use **CC BY-NC 4.0**, requiring
attribution and noncommercial use subject to `LICENSE`. Retain `NOTICE`.
Qwen's base model retains Apache-2.0 (`BASE_MODEL_LICENSE`); the adapter terms
do not relicense it. Code uses PolyForm Noncommercial 1.0.0.

## Citation

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
