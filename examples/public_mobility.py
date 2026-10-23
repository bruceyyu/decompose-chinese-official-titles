"""Reproduce component-specific, three-year mobility using public CGED-Q tables.

No model, GPU, API, private dataset, or new person linkage is used. Input tables
are downloaded separately. This example saves aggregates only, never person rows.
See docs/public_mobility.md for the input contract and differences from the paper.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import json
from pathlib import Path
import platform

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix

SOURCE_KEYS = ["阳历年份", "季节号", "序号", "插补号"]
KEYS = ["year", "season", "sequence", "interpolation"]
RANKS = ["duty_office_rank", "base_office_rank", "additional_title_rank", "qualification_title_rank"]
PARSED_FIELDS = ["duty_office", "base_office", *RANKS]
WINDOWS = [(1760, 1798), (1850, 1864), (1900, 1912)]
GAP = 3
SEED = 20261006
OUTCOMES = ["office", "additional", "eligibility", "title_without_office"]
RULES = {"retained": ("additional_retained", "eligibility_retained"),
         "printed": ("additional", "eligibility"),
         "retained_3y": ("additional_retained_3y", "eligibility_retained_3y")}
COLORS = {"office": "#A51C1C", "additional": "#2E7D32", "eligibility": "#B35900"}


def sha256(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read_table(path, parsed):
    fields = PARSED_FIELDS if parsed else ["person_id"]
    d = pd.read_csv(path, sep="\t", dtype="string", usecols=SOURCE_KEYS + fields)
    audit = {"filename": Path(path).name, "sha256": sha256(path), "input_rows": len(d)}
    numeric = d[SOURCE_KEYS].apply(pd.to_numeric, errors="coerce")
    if (d[SOURCE_KEYS].notna() & numeric.isna()).any(axis=None):
        raise ValueError("A nonempty record-key value is not numeric; inspect the public export.")
    empty = numeric.isna().all(axis=1)
    if numeric.loc[~empty].isna().any(axis=None):
        raise ValueError("Partial or invalid record keys; inspect the input rather than guessing a match.")
    if not parsed and d.loc[empty, "person_id"].notna().any():
        raise ValueError("A person identifier occurs on a row without record keys.")
    audit["rows_without_record_keys"] = int(empty.sum())
    d, numeric = d.loc[~empty].copy(), numeric.loc[~empty].astype(float)
    y, season = numeric[SOURCE_KEYS[0]], numeric[SOURCE_KEYS[1]]
    if parsed:
        if not (y.eq(np.floor(y)).all() and season.isin(range(4)).all()):
            raise ValueError("Parsed table requires calendar years and season indices 0–3.")
    else:
        # This public export uses decimal edition years and seasons 1–4.
        # Season 0 denotes an unspecified season and corresponds to fraction 0.
        if not season.isin(range(5)).all():
            raise ValueError("Person-ID table requires season codes 0–4.")
        season = (season - 1).clip(lower=0)
        if not np.allclose((y - np.floor(y)) * 4, season):
            raise ValueError("Edition-year fractions disagree with season codes.")
    numeric[SOURCE_KEYS[0]], numeric[SOURCE_KEYS[1]] = np.floor(y), season
    if not np.equal(numeric, np.floor(numeric)).all(axis=None):
        raise ValueError("Record-key components must be integers after year/season normalization.")
    d = pd.concat([numeric.rename(columns=dict(zip(SOURCE_KEYS, KEYS))).astype("int64"), d[fields]], axis=1)
    if d.duplicated(KEYS).any():
        raise ValueError("Duplicate normalized record keys; a one-to-one merge is not possible.")
    audit["keyed_rows"] = len(d)
    return d, audit


def valid_rank(s):
    s = pd.to_numeric(s, errors="coerce").astype(float)
    return s.where(s.between(1, 9.5))


def load_records(parsed_path, people_path, start_year=None, end_year=None):
    parsed, pa = read_table(parsed_path, True)
    people, pe = read_table(people_path, False)
    d = parsed.merge(people, on=KEYS, how="outer", validate="one_to_one", indicator=True)
    match = {k: int(v) for k, v in d["_merge"].value_counts().items()}
    if not d["_merge"].eq("both").all():
        raise ValueError(f"The public tables do not cover identical record keys: {match}")
    audit = {"parsed_input": pa, "people_input": pe, "merge": match}
    d = d.drop(columns="_merge")
    audit["interpolated_rows_excluded"] = int(d.interpolation.ne(0).sum())
    d = d.loc[d.interpolation.eq(0)].copy()
    audit["missing_person_id_rows_excluded"] = int(d.person_id.isna().sum())
    d = d.dropna(subset=["person_id"]).copy()
    d["window"] = pd.Series(pd.NA, index=d.index, dtype="string")
    for lo, hi in WINDOWS:
        d.loc[d.year.between(lo, hi), "window"] = f"{lo}-{hi}"
    if d.window.isna().any():
        raise ValueError("Years outside the documented public-release windows; review WINDOWS first.")
    if start_year is not None:
        d = d.loc[d.year.ge(start_year)].copy()
    if end_year is not None:
        d = d.loc[d.year.le(end_year)].copy()
    if d.empty:
        raise ValueError("No linked public records remain in the selected years.")
    # Labels describe the records actually selected, including a 1905 cutoff,
    # rather than misleadingly displaying the source's unfiltered 1912 end.
    labels = {str(w): f"{int(g.year.min())}-{int(g.year.max())}"
              for w, g in d.groupby("window", observed=True)}
    d["window"] = d.window.map(labels)
    d["office"] = valid_rank(d.duty_office_rank)
    d["post"] = d.duty_office.copy()
    # Keep independent-department and ordinary-department magistrates distinct,
    # using the already contextualized public rank, not a new private lookup.
    d.loc[d.duty_office.eq("知州") & d.office.eq(5), "post"] = "直隸州知州"
    base = valid_rank(d.base_office_rank)
    fallback = d.office.isna() & base.notna()
    d.loc[fallback, "office"] = base[fallback]
    d.loc[fallback, "post"] = d.loc[fallback, "base_office"]
    d["additional"] = valid_rank(d.additional_title_rank)
    d["eligibility"] = valid_rank(d.qualification_title_rank)
    # This stable order implements the year's last ranked record, as in the
    # manuscript. Sequence supplies an explicit tie-break within an edition.
    d = d.sort_values(["window", "person_id", "year", "season", "sequence"], kind="mergesort")
    audit.update({"selected_records": len(d), "records_using_base_office": int(fallback.reindex(d.index).sum()),
                  "selected_first_year": int(d.year.min()), "selected_last_year": int(d.year.max()),
                  "unavailable_internal_filters": ["invalid_record", "duplicated_record", "exclude_record", "inconsistent_post", "zsbl"],
                  "new_person_linkage": False, "rank_recalculation": False})
    return d, audit


def person_years(d):
    keys = ["window", "person_id", "year"]
    last = d.dropna(subset=["office"]).groupby(keys, observed=True)[["office", "post"]].last()
    return (d.groupby(keys, observed=True).agg(additional=("additional", "min"), eligibility=("eligibility", "min"))
            .join(last, how="left").reset_index().sort_values(keys, kind="mergesort").reset_index(drop=True))


def retained_component(x, column, max_years=None):
    """Retain a printed component until a post change or rank catch-up.

    State resets at every public-release window. Unreleased decades are not
    treated as observed years, and no title is supplied from before a window.
    """
    result = x[column].to_numpy(float).copy()
    previous_key, last_rank, last_year, last_post = None, np.nan, -1, None
    for i, row in enumerate(x[["window", "person_id", "year", "office", "post"]].itertuples(index=False, name=None)):
        window, person, year, office, post = row
        key = (window, person)
        if key != previous_key:
            previous_key, last_rank, last_year, last_post = key, np.nan, -1, None
        if np.isfinite(last_rank) and (office <= last_rank or post != last_post or
                                      (max_years is not None and year - last_year > max_years)):
            last_rank = np.nan
        if np.isfinite(result[i]):
            last_rank, last_year, last_post = result[i], year, post
        elif np.isfinite(last_rank):
            result[i] = last_rank
    return result


def higher(start, end):
    return end.notna() & (start.isna() | end.lt(start))


def outcome_flags(p, additional, eligibility):
    office = p.office_end.lt(p.office)
    a = higher(p[additional], p[additional + "_end"])
    e = higher(p[eligibility], p[eligibility + "_end"])
    return {"office": office, "additional": a, "eligibility": e,
            "title_without_office": (a | e) & ~office}


def make_pairs(py):
    x = py.loc[py.office.notna()].copy().reset_index(drop=True)
    if x.post.isna().any():
        raise ValueError("A ranked person-year lacks an office name; cannot apply the post-change rule safely.")
    for component in ("additional", "eligibility"):
        x[component + "_retained"] = retained_component(x, component)
        x[component + "_retained_3y"] = retained_component(x, component, max_years=3)
    keys = ["window", "person_id", "year"]
    cols = keys + ["office"] + [field for fields in RULES.values() for field in fields]
    end = x[cols].copy()
    end["year"] -= GAP
    p = x[cols].merge(end, on=keys, suffixes=("", "_end"), validate="one_to_one")
    if p.empty:
        raise ValueError("No officials have ranked offices in public years exactly three years apart.")
    return x, reporting_groups(p, 5)


def reporting_groups(p, years=5):
    """Pool starting years in nonoverlapping groups anchored to each window.

    Only reporting changes; every row remains an exactly three-year comparison.
    For example, two-year groups in the late window start in 1900, 1902, etc.
    """
    if not isinstance(years, int) or years < 1:
        raise ValueError("Reporting-group length must be a positive integer.")
    result = p.copy()
    origin = result.window.str.split("-", n=1).str[0].astype(int)
    result["period"] = origin + (result.year - origin) // years * years
    return result


def summarize(p, draws, seed, report_years=5):
    p = reporting_groups(p, report_years)
    names, flags = [], []
    for rule, (additional, eligibility) in RULES.items():
        for outcome, values in outcome_flags(p, additional, eligibility).items():
            names.append((rule, outcome))
            flags.append(values.to_numpy())
    person, ids = pd.factorize(p.person_id, sort=True)
    rng = np.random.default_rng(seed)
    tables = []
    for resolution in ("window", "reporting_group"):
        group_keys = ["window"] + (["period"] if resolution == "reporting_group" else [])
        groups = p[group_keys].drop_duplicates().sort_values(group_keys).reset_index(drop=True)
        groups["group"] = np.arange(len(groups))
        group = p[group_keys].merge(groups, on=group_keys, how="left", validate="many_to_one")["group"].to_numpy()
        f = np.column_stack(flags + [np.ones(len(p), dtype=bool)]).astype(float)
        row, component = np.nonzero(f)
        k = f.shape[1]
        m = coo_matrix((f[row, component], (person[row], group[row] * k + component)),
                       shape=(len(ids), len(groups) * k)).tocsr()
        counts = np.asarray(m.sum(axis=0)).reshape(len(groups), k)
        samples = np.empty((draws, len(groups), k - 1))
        for b in range(draws):
            weights = np.bincount(rng.integers(len(ids), size=len(ids)), minlength=len(ids))
            c = np.asarray(m.T @ weights).reshape(len(groups), k)
            samples[b] = np.divide(100 * c[:, :-1], c[:, [-1]], out=np.full_like(c[:, :-1], np.nan), where=c[:, [-1]] > 0)
        rows = []
        for g, metadata in groups.drop(columns="group").iterrows():
            mask = group == g
            for j, (rule, outcome) in enumerate(names):
                low, high = np.nanpercentile(samples[:, g, j], [2.5, 97.5])
                rows.append({**metadata.to_dict(), "rule": rule, "outcome": outcome,
                             "pairs": int(counts[g, -1]), "officials": int(p.loc[mask, "person_id"].nunique()),
                             "first_start_year": int(p.loc[mask, "year"].min()), "last_start_year": int(p.loc[mask, "year"].max()),
                             "observed_start_years": int(p.loc[mask, "year"].nunique()),
                             "reporting_group_years": report_years,
                             "events": int(counts[g, j]), "pct": 100 * counts[g, j] / counts[g, -1],
                             "low": float(low), "high": float(high), "bootstrap_draws": draws})
        tables.append(pd.DataFrame(rows))
    return tables


def initial_year_sensitivity(p):
    """Point estimates after allowing three calendar years of public history.

    A window with no remaining intervals is reported with zero pairs and no
    estimated rate, not silently replaced by the full-window estimate.
    """
    rows = []
    for window, group in p.groupby("window", observed=True):
        first_year = int(str(window).split("-", 1)[0])
        later = group.loc[group.year.ge(first_year + GAP)]
        for rule, fields in RULES.items():
            for outcome, flag in outcome_flags(later, *fields).items():
                rows.append({"window": window, "rule": rule, "outcome": outcome,
                             "earliest_allowed_start": first_year + GAP,
                             "pairs": len(later), "events": int(flag.sum()),
                             "pct": float(100 * flag.mean()) if len(later) else np.nan})
    return pd.DataFrame(rows)


def plot_rates(table, output, report_years=5):
    d = table.loc[table.rule.eq("retained")]
    windows = list(d.window.drop_duplicates())
    with plt.rc_context({"font.family": "STIXGeneral", "font.size": 9,
                         "axes.spines.top": False, "axes.spines.right": False,
                         "axes.edgecolor": "#555555", "savefig.facecolor": "white"}):
        if len(windows) == 1:
            fig, panels = plt.subplots(1, 2, figsize=(7.8, 3.0), constrained_layout=True)
            axes = np.asarray(panels).reshape(2, 1)
        else:
            fig, axes = plt.subplots(2, len(windows), figsize=(max(6.5, 3.1 * len(windows)), 5.3),
                                     squeeze=False, sharey="row", constrained_layout=True)
        limits = {}
        for row, outcomes in enumerate([["office"], ["additional", "eligibility"]]):
            limits[row] = max(1.0 if row else 5.0, float(d.loc[d.outcome.isin(outcomes), "high"].max()) * 1.17)
        for col, window in enumerate(windows):
            for row, outcomes in enumerate([["office"], ["additional", "eligibility"]]):
                ax = axes[row, col]
                for outcome in outcomes:
                    s = d.loc[d.window.eq(window) & d.outcome.eq(outcome)].sort_values("period")
                    # Leave genuinely unobserved reporting groups disconnected.
                    for _, segment in s.groupby(s.period.diff().fillna(report_years).ne(report_years).cumsum()):
                        ax.plot(segment.period, segment.pct, marker="o", ms=3, lw=1.1, color=COLORS[outcome])
                        if len(segment) > 1:
                            ax.fill_between(segment.period.to_numpy(float), segment.low.to_numpy(float),
                                            segment.high.to_numpy(float), color=COLORS[outcome], alpha=.15, linewidth=0)
                        else:
                            ax.errorbar(segment.period, segment.pct,
                                        yerr=[segment.pct - segment.low, segment.high - segment.pct],
                                        fmt="none", capsize=3, color=COLORS[outcome], lw=.9)
                ax.set_ylim(0, limits[row])
                ticks = sorted(d.loc[d.window.eq(window), "period"].unique())
                # Keep annual panels legible without removing observations.
                ax.set_xticks(ticks[::max(1, int(np.ceil(len(ticks) / 7)))])
                margin = max(.6, report_years * .4)
                ax.set_xlim(min(ticks) - margin, max(ticks) + margin)
                ax.grid(axis="y", color="#E6E6E6", lw=.5)
                ax.set_axisbelow(True)
                if len(windows) == 1:
                    ax.set_title("A. Promoted to a higher office" if row == 0 else
                                 "B. Higher additional title or eligibility", loc="left", fontsize=9)
                elif row == 0:
                    ax.set_title(f"Public records: {window}", loc="left", fontsize=10)
                if row == 1 or len(windows) == 1:
                    ax.set_xlabel("Comparison starting year" if report_years == 1 else
                                  f"Start of {report_years}-year reporting group")
            if len(windows) > 1:
                axes[0, col].text(.03, .96, "Higher office", transform=axes[0, col].transAxes, va="top", color=COLORS["office"])
        if len(windows) == 1:
            for ax in panels:
                ax.set_ylabel("Three-year advancement (%)")
        else:
            axes[0, 0].set_ylabel("A. Promoted within three years (%)")
            axes[1, 0].set_ylabel("B. Advanced in title within three years (%)")
        fig.legend([Line2D([], [], color=COLORS[k], marker="o", lw=1) for k in ["additional", "eligibility"]],
                   ["Higher additional title", "Eligibility for higher office"], loc="outside lower center", ncol=2, frameon=False)
        fig.suptitle(f"Public CGED-Q JSL records: {windows[0]}" if len(windows) == 1 else
                     "Component-specific mobility in public CGED-Q JSL records", fontsize=12)
        for suffix in ("png", "pdf"):
            fig.savefig(output / f"component_mobility.{suffix}", dpi=220)
        plt.close(fig)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parsed", type=Path, required=True)
    ap.add_argument("--people", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--start-year", type=int, default=1850,
                    help="First record year to include (default 1850).")
    ap.add_argument("--end-year", type=int, default=1864,
                    help="Last record year to include (default 1864).")
    ap.add_argument("--report-years", type=int, default=2,
                    help="Nonoverlapping groups of comparison starting years (default 2); mobility stays three-year.")
    ap.add_argument("--draws", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=SEED)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()
    if args.draws < 100:
        ap.error("Use at least 100 person-bootstrap draws (default 1,000).")
    if args.report_years < 1:
        ap.error("--report-years must be a positive integer")
    if args.start_year is not None and args.end_year is not None and args.start_year > args.end_year:
        ap.error("--start-year must not exceed --end-year")
    if args.output.exists() and any(args.output.iterdir()) and not args.overwrite:
        ap.error("Output directory is not empty; choose a new one or explicitly pass --overwrite.")
    d, audit = load_records(args.parsed, args.people, args.start_year, args.end_year)
    py = person_years(d)
    ranked, pairs = make_pairs(py)
    window_rates, group_rates = summarize(pairs, args.draws, args.seed, args.report_years)
    audit.update({"analysis_code_sha256": sha256(__file__),
                  "python": platform.python_version(), "dependencies": {name: importlib.metadata.version(name) for name in ["numpy", "pandas", "scipy", "matplotlib"]},
                  "person_years": len(py), "office_ranked_person_years": len(ranked), "three_year_pairs": len(pairs),
                  "pair_officials": int(pairs.person_id.nunique()), "gap_years": GAP, "reporting_group_years": args.report_years,
                  "reporting_group_anchor": "first year of each selected public window",
                  "draws": args.draws, "seed": args.seed, "start_year_filter": args.start_year, "end_year_filter": args.end_year,
                  "component_history_resets_at_window_boundaries": True,
                  "observed_record_years": {str(w): sorted(g.year.unique().tolist()) for w, g in d.groupby("window", observed=True)},
                  "observed_pair_start_years": {str(w): sorted(g.year.unique().tolist()) for w, g in pairs.groupby("window", observed=True)},
                  "not_an_exact_manuscript_replication": True})
    coverage = (d.groupby(["window", "year"], observed=True).agg(records=("person_id", "size"), officials=("person_id", "nunique"))
                .join(pairs.groupby(["window", "year"], observed=True).size().rename("three_year_pairs"), how="left").fillna(0).reset_index())
    args.output.mkdir(parents=True, exist_ok=True)
    window_rates.to_csv(args.output / "window_rates.csv", index=False)
    group_rates.to_csv(args.output / "reporting_group_rates.csv", index=False)
    if args.report_years == 5:
        group_rates.to_csv(args.output / "five_year_rates.csv", index=False)
    initial_year_sensitivity(pairs).to_csv(args.output / "initial_year_sensitivity.csv", index=False)
    coverage.to_csv(args.output / "annual_coverage.csv", index=False)
    (args.output / "provenance.json").write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    plot_rates(group_rates, args.output, args.report_years)
    print(f"Matched {audit['merge']['both']:,} public records; {len(pairs):,} three-year pairs, {audit['pair_officials']:,} officials.")
    print(window_rates.query("rule == 'retained'")[["window", "outcome", "pairs", "events", "pct", "low", "high"]].to_string(index=False))
    print(f"Aggregates and figure saved to: {args.output}")


if __name__ == "__main__":
    main()
