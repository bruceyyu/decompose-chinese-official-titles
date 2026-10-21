"""Command-line interface with explicit model, input, and output choices."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .ranks import rank_record
from .schema import json_schema, validate_record


def _read(path: Path):
    with path.open(encoding="utf-8") as source:
        for line_no, line in enumerate(source, 1):
            if line.strip():
                try:
                    yield json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON on line {line_no}") from exc


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Decompose official titles and keep component ranks separate")
    commands = parser.add_subparsers(dest="command", required=True)
    schema = commands.add_parser("schema", help="Print the canonical output JSON Schema; no model required")
    schema.add_argument("--task", choices=("qing", "joseon"), default="qing")
    for command in ("validate", "rank", "parse"):
        sub = commands.add_parser(command)
        sub.add_argument("--input", type=Path, required=True, help="Input JSONL file")
        sub.add_argument("--output", type=Path, required=True, help="New output file (will not overwrite)")
        if command != "rank":
            sub.add_argument("--task", choices=("qing", "joseon"), default="qing")
        if command == "parse":
            sub.add_argument("--adapter", required=True, help="PEFT adapter folder or Hugging Face repository ID")
            sub.add_argument("--base-model", default="Qwen/Qwen3.5-4B")
            sub.add_argument("--device-map", default="auto", help="auto, cpu, mps, or a device such as cuda:0")
            sub.add_argument("--with-ranks", action="store_true")
    args = parser.parse_args(argv)
    if args.command == "schema":
        print(json.dumps(json_schema(args.task), ensure_ascii=False, indent=2))
        return
    if args.input.resolve() == args.output.resolve() or args.output.exists():
        parser.error("Output must be a new file distinct from input")
    if not args.input.is_file():
        parser.error("Input file does not exist")
    model = None
    if args.command == "parse":
        if args.with_ranks and args.task != "qing":
            parser.error("The Qing rank lookup must not be applied to Joseon titles")
        from .inference import LocalParser
        model = LocalParser(args.adapter, task=args.task, base_model=args.base_model,
                            device_map=args.device_map)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    failures = 0
    with args.output.open("x", encoding="utf-8") as output:
        for index, value in enumerate(_read(args.input)):
            try:
                if args.command == "parse":
                    title = value if isinstance(value, str) else value["original_title"]
                    result = model.parse(title)
                    if args.with_ranks:
                        result = {**result, **rank_record(result)}
                else:
                    result = validate_record(value, getattr(args, "task", "qing"))
                    if args.command == "rank":
                        result = {**result, **rank_record(result)}
                output.write(json.dumps(result, ensure_ascii=False, allow_nan=False) + "\n")
            except (ValueError, KeyError, TypeError) as exc:
                failures += 1
                output.write(json.dumps({"index": index, "error": str(exc)}, ensure_ascii=False) + "\n")
    print(f"Wrote output; failed records: {failures}", file=sys.stderr)
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()

