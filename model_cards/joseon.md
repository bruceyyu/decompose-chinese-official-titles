---
base_model: Qwen/Qwen3.5-4B
library_name: peft
license: cc-by-nc-4.0
language:
  - ko
tags:
  - historical-text
  - information-extraction
  - lora
  - joseon
---

# Joseon Korean-script official-title decomposition adapter

A separate LoRA adapter for **Qwen/Qwen3.5-4B**, trained to identify departments
and posts in the Korean-script form of Joseon official titles. It is **not** the
Qing adapter applied zero-shot, and it does not predict Qing ranks. The case
demonstrates adaptation of the procedure to another institutional schema and
script, not an unchanged model's universal historical expertise.

Related manuscript: *Office, Rank, and Mobility: Decomposing Historical Chinese
Bureaucratic Titles with Language Models*, Yue Yu, Jun Chen, Michael Yan Hon
Chung, and Cameron Campbell.

Preprint: https://osf.io/preprints/socarxiv/eg87f_v1

Code and installation: https://github.com/bruceyyu/decompose-chinese-official-titles

## Use

Install the codebase with `pip install -e '.[inference]'`, download this adapter
folder, and run:

```bash
official-titles parse --task joseon --adapter /path/to/adapter \
  --input my-korean-titles.jsonl --output my-components.jsonl
```

Use the exact `prompt.txt`, disable thinking, decode greedily, and allow up to
256 new tokens. Output has `original_title`, `department`, and `position`.
The latter two fields are strings or null. The prompt asks for components
actually printed in the Korean-script title, not restoration of an unstated
institutional hierarchy. Do not use the Qing fifteen-field prompt.

## Source, adaptation, and selection

The source is the third-party JoseonTSI career-record collection:
https://github.com/dhchoi02/JoseonTSI . Source files are obtained separately and
remain subject to their original terms. Preparation strips parenthetical forms,
screens Korean-script titles, deduplicates that form, and constructs 1,000
adaptation and 250 disjoint evaluation titles, using seed 20260930.

Five-fold cross-validation within the 1,000-title adaptation pool selected
learning rate 5e-4, four epochs, rank-32 LoRA, batch size 32,
shuffle seed 42, maximum sequence length 3,000, and thinking disabled.
The released checkpoint is trained on all
1,000 adaptation titles. The 250 evaluation titles are not training or
cross-validation inputs. This is the Korean-script benchmark, not the earlier
mixed-script pilot.

## Evaluation

On the 250-title holdout: department exact agreement 97.2%, position exact
agreement 98.0%, component average 97.6%, both components correct 95.2%, and
schema validity 100%. These are agreements with the benchmark's source-derived
targets, not independent expert verification of all Joseon institutional roles.
They do not establish performance on every Korean historical source.

Adaptation rows, held-out answers, row-level predictions with answers, and the
third-party source collection are **not bundled**. Training configurations are
provided, but training and evaluation scripts are not. The experiment is not fully
reproducible from the release alone.

## Limitations and export

New scripts, mixed-script forms, OCR errors, and different institutions require
validation. Correct JSON is not evidence of a correct institutional reading.
Exporting and checking tensor structure does not establish identical local
inference or verify accuracy in the converted runtime. Consult
`export_manifest.json` and `verification.json`. Do not use the
model for consequential decisions about living individuals.

The Transformers-compatible export joins the separate Q/K/V adapter matrices
into each fused projection and preserves their scaling; its fused LoRA rank is
96, while the training rank was 32. The unembedding adapter targets `lm_head`,
not the input embedding. Use the adapter without merging into tied base weights
unless the merged runtime has been independently validated. Structural and
matrix-preservation checks and a two-example local generation smoke test are
recorded in `verification.json`. Neither is an exported-runtime accuracy benchmark.

## Files and licensing

This package contains only adapter weights/configuration, this card, the prompt,
schema, and checksum manifest. It contains no base weights, private labels,
credentials, or person-level career records. The authors' adapter contributions
and model materials use **CC BY-NC 4.0**, requiring attribution and
noncommercial use subject to the full `LICENSE`. Retain the attribution in
`NOTICE`. The independently obtained Qwen base model retains Apache-2.0
(`BASE_MODEL_LICENSE`); the adapter terms do not relicense it. The software uses
PolyForm Noncommercial 1.0.0.

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
