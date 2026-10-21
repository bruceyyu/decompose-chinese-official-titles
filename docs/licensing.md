# Attribution and noncommercial release

At the maintainer's direction, the original software is offered under
**PolyForm Noncommercial License 1.0.0**. Keep `LICENSE` and the `Required Notice:`
attribution lines in `NOTICE` when distributing copies. The license permits
noncommercial purposes, defines personal research uses, and expressly includes
the listed educational/public/noncommercial organizations; its full definitions
govern, not a shorthand claim that every institution's activity is forbidden.
The release is source-available, not unrestricted or OSI open-source software.
Official text: https://polyformproject.org/licenses/noncommercial/1.0.0 .

The authors' adapter contributions, model cards, prompt/schema assets,
documentation, aggregate results, and original lookup-table compilation are
offered under **CC BY-NC 4.0**, to the extent they are protected by rights the
authors hold. Retain attribution, link to the license, and indicate changes when
sharing. The original institutional facts and public-domain material are not
made private property by inclusion here. Complete text is in
`licenses/CC-BY-NC-4.0.txt`; official terms:
https://creativecommons.org/licenses/by-nc/4.0/ .

These noncommercial terms do not authorize commercial uses outside their scope;
such uses require separate permission where the authors hold the relevant
rights. Copyright exceptions and limitations remain applicable. Contributors
must have authority to offer their contributions under the selected licenses.
The project should not claim that a license guarantees enforceability in every
jurisdiction or controls material outside the authors' rights.

Human annotations are deliberately excluded: no license or access-on-request
promise is made for them. Withholding label files does not guarantee that a
trained model cannot reproduce some training examples, and it does not replace
transparent reporting of annotation and evaluation limitations.

## Base model and third-party material

Qwen/Qwen3.5-4B is independently distributed under **Apache 2.0**:
https://huggingface.co/Qwen/Qwen3.5-4B . Base weights are not included. The
noncommercial adapter license does not relicense the base model. Its Apache
text is included separately as `licenses/Apache-2.0.txt`, and exported adapter
folders preserve the base-model attribution and license separately.

Transformers, PEFT, and other dependencies are installed,
not vendored or relicensed here. JoseonTSI and NIKH material are not mirrored;
consult their original distribution terms. CGED-Q data remain subject to the
conditions at https://doi.org/10.7910/DVN/GMQWVZ . The consolidated rank table
retains source and variant notes; it contains institutional mappings, not individual
annotation or roster rows. See `src/title_ranks/README.md` for provenance.
