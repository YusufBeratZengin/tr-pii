import io
import json
import unittest
from pathlib import Path

from tr_pii.cli import main

GOLDEN_SCAN = (
    '{"type": "EMAIL", "start": 9, "end": 30, '
    '"value": "dummy@example.invalid", "confidence": 0.99}\n'
    '{"type": "TCKN", "start": 37, "end": 48, '
    '"value": "29141777626", "confidence": 0.99}\n'
)

GOLDEN_MASK = "E-posta: *********************\nTCKN: *********26\n"


class ExampleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.sample_path = Path(__file__).parent.parent / "examples" / "sample.txt"
        self.assertTrue(self.sample_path.is_file(), f"Missing example file: {self.sample_path}")

    def test_example_scan_output(self) -> None:
        output = io.StringIO()
        status = main(["scan", str(self.sample_path)], stdout=output)
        self.assertEqual(status, 3)
        self.assertEqual(output.getvalue(), GOLDEN_SCAN)

    def test_example_scan_count_output(self) -> None:
        output = io.StringIO()
        status = main(["scan", str(self.sample_path), "--count"], stdout=output)
        self.assertEqual(status, 3)
        self.assertEqual(output.getvalue(), "2\n")

        output_json = io.StringIO()
        status_json = main(
            ["scan", str(self.sample_path), "--count", "--format", "json"], stdout=output_json
        )
        self.assertEqual(status_json, 3)
        self.assertEqual(json.loads(output_json.getvalue()), {"count": 2})

    def test_example_mask_partial_output(self) -> None:
        output = io.StringIO()
        status = main(["mask", "--style", "partial", str(self.sample_path)], stdout=output)
        self.assertEqual(status, 3)
        self.assertEqual(output.getvalue(), GOLDEN_MASK)


if __name__ == "__main__":
    unittest.main()
