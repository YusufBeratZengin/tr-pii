import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tr_pii import fake
from tr_pii.cli import main


class CLITests(unittest.TestCase):
    def invoke(self, args: list[str], text: str = "") -> tuple[int, str, str]:
        output = io.StringIO()
        errors = io.StringIO()
        result = main(args, stdin=io.StringIO(text), stdout=output, stderr=errors)
        return result, output.getvalue(), errors.getvalue()

    def test_scan_json_lines_and_exit_codes(self) -> None:
        value = fake.tckn(seed=27)
        status, output, errors = self.invoke(["scan", "-"], value + ";dummy@example.invalid")
        self.assertEqual(status, 3)
        records = [json.loads(line) for line in output.splitlines()]
        self.assertEqual([record["type"] for record in records], ["TCKN", "EMAIL"])
        self.assertEqual(records[0]["value"], value)
        self.assertEqual(set(records[0]), {"type", "start", "end", "value", "confidence"})
        self.assertEqual(errors, "")
        self.assertEqual(self.invoke(["scan", "-"], "plain"), (0, "", ""))
        self.assertEqual(self.invoke(["scan", "-"], ""), (0, "", ""))

    def test_mask_output_filter_and_clean_code(self) -> None:
        self.assertEqual(self.invoke(["mask", "-"], "dummy@example.invalid"), (3, "[EMAIL]", ""))
        self.assertEqual(self.invoke(["mask", "-"], "plain\n"), (0, "plain\n", ""))
        self.assertEqual(self.invoke(["mask", "-", "--types", "TCKN"], "dummy@example.invalid"),
                         (0, "dummy@example.invalid", ""))
        self.assertEqual(self.invoke(["mask", "-", "--style", "stars"], "dummy@example.invalid"),
                         (3, "*" * 21, ""))

    def test_hash_environment_salt(self) -> None:
        with patch.dict(os.environ, {"TR_PII_SALT": "public-test-salt"}):
            status, output, _ = self.invoke(
                ["mask", "-", "--style", "hash"], "dummy@example.invalid"
            )
            self.assertEqual(status, 3)
            self.assertRegex(output, r"\[EMAIL:[a-f0-9]{16}\]")
        with patch.dict(os.environ, {"TR_PII_SALT": ""}):
            status, output, error = self.invoke(["mask", "-", "--style", "hash"])
            self.assertEqual(status, 2)
            self.assertEqual(output, "")
            self.assertIn("hash salt", error)

    def test_files_terms_and_invalid_utf8(self) -> None:
        # Place temporary test files in the checkout; no external data is read.
        paths: list[Path] = []
        for _ in range(2):
            descriptor, filename = tempfile.mkstemp(dir=Path.cwd() / "is", suffix=".txt")
            os.close(descriptor)
            paths.append(Path(filename))
        text, terms = paths
        try:
            text.write_bytes("İZİN\n".encode())
            terms.write_text("izin\n\n", encoding="utf-8")
            self.assertEqual(self.invoke(["mask", str(text), "--terms-file", str(terms)]),
                             (3, "[CUSTOM]\n", ""))
            text.write_bytes(b"plain\r\nsecond line\r\n")
            self.assertEqual(
                self.invoke(["mask", str(text)]), (0, "plain\r\nsecond line\r\n", "")
            )
            text.write_bytes(b"\xff")
            status, output, error = self.invoke(["scan", str(text)])
            self.assertEqual(status, 2)
            self.assertEqual(output, "")
            self.assertIn("UTF-8", error)
            status, _, error = self.invoke(["scan", str(text.with_suffix(".missing"))])
            self.assertEqual(status, 2)
            self.assertNotIn(str(text), error)
        finally:
            for path in paths:
                path.unlink()

    def test_invalid_options_no_input_disclosure(self) -> None:
        status, output, error = self.invoke(
            ["scan", "-", "--types", "INVALID"], "private-test-input"
        )
        self.assertEqual(status, 2)
        self.assertEqual(output, "")
        self.assertNotIn("private-test-input", error)
        self.assertNotIn("INVALID", error)

    def test_module_subprocess_exit_and_utf8(self) -> None:
        result = subprocess.run([sys.executable, "-m", "tr_pii", "mask", "-"],
                                input="İçerik: dummy@example.invalid\n", text=True,
                                encoding="utf-8", capture_output=True, check=False)
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertEqual(result.stdout, "İçerik: [EMAIL]\n")
        result = subprocess.run([sys.executable, "-m", "tr_pii", "scan", "-"],
                                input="plain", text=True, encoding="utf-8",
                                capture_output=True, check=False)
        self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()

