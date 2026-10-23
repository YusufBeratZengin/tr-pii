"""Render the README terminal demo from real CLI output; no external tools needed."""

import argparse
import os
import subprocess
import sys
from html import escape
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "docs" / "demo.svg"
COMMANDS: tuple[tuple[tuple[str, ...], int], ...] = (
    (("--version",), 0),
    (("scan", "examples/sample.txt", "--count", "--format", "json"), 3),
    (("mask", "examples/sample.txt"), 3),
    (("mask", "examples/sample.txt", "--style", "stars"), 3),
    (("mask", "--style", "partial", "examples/sample.txt"), 3),
)


def render() -> str:
    """Capture each command, validate its status and escape its output as SVG text."""
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONIOENCODING="utf-8")
    lines: list[tuple[str, str]] = []
    for args, expected_status in COMMANDS:
        result = subprocess.run(
            [sys.executable, "-m", "tr_pii", *args],
            cwd=ROOT,
            env=env,
            text=True,
            encoding="utf-8",
            capture_output=True,
            check=False,
            timeout=30,
        )
        if result.returncode != expected_status or result.stderr:
            raise RuntimeError("Demo command failed: python -m tr_pii " + " ".join(args))
        if lines:
            lines.append(("", "#d6deeb"))
        lines.append(("$ python -m tr_pii " + " ".join(args), "#8ee6b0"))
        lines.extend((line, "#d6deeb") for line in result.stdout.splitlines())

    height = 122 + 25 * len(lines)
    rows = "\n".join(
        f'    <text x="28" y="{88 + 25 * index}" fill="{color}">{escape(line)}</text>'
        for index, (line, color) in enumerate(lines)
    )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="960" height="{height}"
     viewBox="0 0 960 {height}" role="img" aria-labelledby="title description">
  <title id="title">tr-pii: offline scanning and masking</title>
  <desc id="description">Real CLI output using the synthetic examples/sample.txt fixture.
    Counts, tag masking, stars and partial masking. Findings return exit code 3.</desc>
  <rect width="960" height="{height}" rx="16" fill="#0d1117"/>
  <path d="M16 0H944Q960 0 960 16V48H0V16Q0 0 16 0Z" fill="#1c2431"/>
  <circle cx="28" cy="24" r="6" fill="#ff605c"/>
  <circle cx="50" cy="24" r="6" fill="#ffbd44"/>
  <circle cx="72" cy="24" r="6" fill="#00ca4e"/>
  <g font-family="ui-monospace, SFMono-Regular, Consolas, monospace" font-size="16">
    <text x="480" y="30" text-anchor="middle" fill="#b6c2d4">tr-pii · offline by default</text>
{rows}
    <text x="28" y="{height - 24}" fill="#9baac0" font-size="14"
      >Synthetic fixture · findings return exit code 3</text>
  </g>
</svg>
'''


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Fail if docs/demo.svg is stale")
    args = parser.parse_args()
    svg = render()
    if args.check:
        if not TARGET.is_file() or TARGET.read_text(encoding="utf-8") != svg:
            print("Demo is stale; run python scripts/make-demo.py", file=sys.stderr)
            return 1
        print("docs/demo.svg matches real CLI output")
    else:
        TARGET.parent.mkdir(parents=True, exist_ok=True)
        with TARGET.open("w", encoding="utf-8", newline="\n") as stream:
            stream.write(svg)
        print("Generated docs/demo.svg from real CLI output")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
