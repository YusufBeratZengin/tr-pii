"""UTF-8 file/stdin CLI. Findings cause exit status 3 for both commands."""

import argparse
import io
import json
import os
import sys
from dataclasses import asdict
from pathlib import Path
from typing import TextIO, cast

from . import TYPES, __version__
from .api import Style, _mask_matches, _validate_style, find


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
        if command == "mask":
            sub.add_argument("--style", choices=("tag", "stars", "partial", "hash"), default="tag")
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
        style = cast(Style, getattr(args, "style", "tag"))
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
            for match in matches:
                output_stream.write(json.dumps(asdict(match), ensure_ascii=False) + "\n")
        else:
            output_stream.write(_mask_matches(text, matches, style, salt))
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
