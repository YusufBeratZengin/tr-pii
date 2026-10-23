"""UTF-8 file/stdin CLI. Findings cause exit status 3 for both commands."""

import argparse
import io
import json
import os
import secrets
import sys
from dataclasses import asdict
from pathlib import Path
from typing import TextIO, cast

from . import TYPES, __version__
from .api import STYLES, Style, _mask_spans, _validate_style, find, stats


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tr-pii", description="Detect and mask Turkish PII offline"
    )
    parser.add_argument("--version", action="version", version=__version__)
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("scan", "mask"):
        sub = commands.add_parser(command)
        sub.add_argument("file", help="UTF-8 input file, or - for stdin")
        sub.add_argument("--types", help="Comma-separated type names: " + ",".join(TYPES))
        sub.add_argument("--terms-file", type=Path, help="UTF-8 custom terms, one per line")
        if command == "scan":
            sub.add_argument(
                "--count", action="store_true", help="Print only the count of findings"
            )
            sub.add_argument(
                "--format",
                choices=("text", "json"),
                default="text",
                help="Output format for count/stats: text (default) or json",
            )
            sub.add_argument(
                "--stats",
                action="store_true",
                help="Print a summary (total, per-type counts) instead of findings",
            )
        if command == "mask":
            sub.add_argument("--style", choices=STYLES, default="tag")
            sub.add_argument(
                "--fake",
                action="store_true",
                help="Shorthand for --style fake (replace with synthetic values)",
            )
            sub.add_argument(
                "--seed",
                type=int,
                help="Seed for --style fake; the same seed gives the same output",
            )
            sub.add_argument(
                "--format",
                choices=("text", "json"),
                default="text",
                help="text (default) prints masked text; json adds offsets of every finding",
            )
            sub.add_argument("-o", "--output", type=Path, help="Write masked text to file")
            sub.add_argument(
                "--force", action="store_true", help="Overwrite output file if it exists"
            )
    return parser


def _read_utf8(path: Path) -> str:
    with path.open(encoding="utf-8", newline="") as stream:
        return stream.read()


def main(
    argv: list[str] | None = None,
    *,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
    stderr: TextIO | None = None,
) -> int:
    """Return 0 (clean), 3 (findings), or 2 (usage/input error)."""
    args = _parser().parse_args(argv)
    input_stream = sys.stdin if stdin is None else stdin
    output_stream = sys.stdout if stdout is None else stdout
    error_stream = sys.stderr if stderr is None else stderr
    try:
        selected = None if args.types is None else args.types.split(",")
        if selected is not None:
            selected = [kind.strip() for kind in selected]
        style = cast(
            Style, "fake" if getattr(args, "fake", False) else getattr(args, "style", "tag")
        )
        salt = os.environ.get("TR_PII_SALT")
        _validate_style(style, salt)
        text = input_stream.read() if args.file == "-" else _read_utf8(Path(args.file))
        terms = (
            ()
            if args.terms_file is None
            else tuple(
                line.strip() for line in _read_utf8(args.terms_file).splitlines() if line.strip()
            )
        )
        matches = find(text, selected, custom_terms=terms)
        if args.command == "scan":
            if getattr(args, "stats", False):
                summary = stats(matches)
                if getattr(args, "format", "text") == "json":
                    output_stream.write(json.dumps(summary, ensure_ascii=False) + "\n")
                else:
                    output_stream.write(f"total: {summary['total']}\n")
                    by_type = cast(dict[str, int], summary["by_type"])
                    for kind, number in by_type.items():
                        output_stream.write(f"{kind}: {number}\n")
            elif getattr(args, "count", False):
                fmt = getattr(args, "format", "text")
                if fmt == "json":
                    output_stream.write(json.dumps({"count": len(matches)}) + "\n")
                else:
                    output_stream.write(f"{len(matches)}\n")
            else:
                for match in matches:
                    output_stream.write(json.dumps(asdict(match), ensure_ascii=False) + "\n")
        else:
            seed = getattr(args, "seed", None)
            if seed is None:
                seed = 0 if style != "fake" else secrets.randbelow(2**32)
            masked, spans = _mask_spans(text, matches, style, salt, seed)
            if getattr(args, "format", "text") == "json":
                findings = [
                    {
                        "type": match.type,
                        "start": match.start,
                        "end": match.end,
                        "masked_start": span[0],
                        "masked_end": span[1],
                        "replacement": span[2],
                    }
                    for match, span in zip(matches, spans, strict=True)
                ]
                masked_json = json.dumps({"text": masked, "findings": findings}, ensure_ascii=False)
                masked = masked_json + "\n"
            output_file = getattr(args, "output", None)
            if output_file is not None:
                output_path = cast(Path, output_file)
                if output_path.exists() and not getattr(args, "force", False):
                    raise FileExistsError(f"Output file already exists: {output_path}")
                output_path.write_text(masked, encoding="utf-8")
            else:
                output_stream.write(masked)
        return 3 if matches else 0
    except (OSError, UnicodeError, ValueError):
        # Do not echo filenames, input, terms, salts or malformed type strings.
        error_stream.write(
            "tr-pii: Unable to process input; check UTF-8 files, options and hash salt.\n"
        )
        return 2


def run() -> None:
    """Configure real console streams for UTF-8 and exit with the CLI status."""
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(encoding="utf-8", newline="")
    raise SystemExit(main())
