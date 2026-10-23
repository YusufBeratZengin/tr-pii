"""Passport, MERSIS, redact/fake styles, stats and JSON offsets."""

import io
import json
import unittest

from tr_pii import (
    STYLES,
    fake,
    find,
    mask,
    stats,
    validate_credit_card,
    validate_mersis,
    validate_passport,
    validate_phone,
    validate_plate,
    validate_postal_code,
    validate_tckn,
    validate_tr_iban,
    validate_vkn,
)
from tr_pii.cli import main


class DetectorTests(unittest.TestCase):
    def test_passport_requires_label_and_shape(self) -> None:
        serial = fake.passport(seed=1)
        self.assertTrue(validate_passport(serial))
        for bad in ("u12345678", "U1234567890", "U123456", "12345678", "UU1234567"):
            self.assertFalse(validate_passport(bad), bad)
        text = f"Pasaport no: {serial}."
        found = find(text, ["PASSPORT"])
        self.assertEqual([(m.type, m.value) for m in found], [("PASSPORT", serial)])
        self.assertEqual(text[found[0].start : found[0].end], serial)
        self.assertEqual(find(f"Referans {serial}", ["PASSPORT"]), [])
        self.assertEqual(len(find("passport: u12345678", ["PASSPORT"])), 1)

    def test_mersis_requires_label_and_16_digits(self) -> None:
        number = fake.mersis(seed=2)
        self.assertTrue(validate_mersis(number))
        dashed = f"{number[:4]}-{number[4:8]}-{number[8:12]}-{number[12:]}"
        self.assertTrue(validate_mersis(dashed))
        self.assertFalse(validate_mersis(number[:-1]))
        self.assertFalse(validate_mersis(number + "1"))
        found = find(f"MERSİS No: {number}")
        self.assertEqual([m.type for m in found], ["MERSIS"])
        self.assertEqual(find(f"seri {number}", ["MERSIS"]), [])

    def test_mersis_beats_card_for_labelled_16_digits(self) -> None:
        number = fake.credit_card(seed=5)
        self.assertEqual([m.type for m in find(f"MERSIS: {number}")], ["MERSIS"])
        self.assertEqual([m.type for m in find(number)], ["CREDIT_CARD"])

    def test_iban_checksum_rejects_lookalikes(self) -> None:
        iban = fake.tr_iban(seed=3)
        self.assertEqual(len(find(iban, ["IBAN"])), 1)
        broken = iban[:-1] + str((int(iban[-1]) + 1) % 10)
        self.assertFalse(validate_tr_iban(broken))
        self.assertEqual(find(broken, ["IBAN"]), [])

    def test_plate_province_codes(self) -> None:
        for code in range(1, 82):
            self.assertTrue(validate_plate(f"{code:02d} ABC 123"), code)
        for bad_code in ("00", "82", "99"):
            self.assertFalse(validate_plate(f"{bad_code} ABC 123"), bad_code)

    def test_vkn_checksum_and_generated(self) -> None:
        for seed in range(25):
            self.assertTrue(validate_vkn(fake.vkn(seed=seed)))
        value = fake.vkn(seed=9)
        broken = value[:-1] + str((int(value[-1]) + 1) % 10)
        self.assertFalse(validate_vkn(broken))


class StyleTests(unittest.TestCase):
    def test_styles_constant(self) -> None:
        self.assertEqual(set(STYLES), {"tag", "stars", "partial", "hash", "redact", "fake"})

    def test_redact_hides_type(self) -> None:
        self.assertEqual(mask("dummy@example.invalid", style="redact"), "[REDACTED]")

    def test_partial_for_new_types(self) -> None:
        serial = fake.passport(seed=4)
        masked = mask(f"pasaport: {serial}", style="partial")
        self.assertEqual(masked, "pasaport: " + "*" * 7 + serial[-2:])

    def test_fake_is_reproducible_and_consistent(self) -> None:
        tckn = fake.tckn(seed=11)
        text = f"{tckn} ve {tckn}"
        one = mask(text, style="fake", seed=7)
        self.assertEqual(one, mask(text, style="fake", seed=7))
        self.assertNotEqual(one, mask(text, style="fake", seed=8))
        self.assertNotIn(tckn, one)
        left, right = one.split(" ve ")
        self.assertEqual(left, right)  # same input value, same fake

    def test_fake_values_are_valid_and_keep_layout(self) -> None:
        cases = {
            "TCKN": (fake.tckn(seed=1), validate_tckn),
            "VKN": (fake.vkn(seed=1), validate_vkn),
            "IBAN": (fake.tr_iban(seed=1), validate_tr_iban),
            "CREDIT_CARD": (fake.credit_card(seed=1), validate_credit_card),
            "PASSPORT": (fake.passport(seed=1), validate_passport),
            "MERSIS": (fake.mersis(seed=1), validate_mersis),
        }
        for kind, (value, validator) in cases.items():
            for seed in range(10):
                replaced = fake.like(kind, value, value, seed)
                self.assertTrue(validator(replaced), (kind, replaced))
                self.assertEqual(len(replaced), len(value))
                self.assertNotEqual(replaced, value)

    def test_fake_phone_plate_postal_ip_email(self) -> None:
        for seed in range(30):
            phone = fake.like("PHONE", "+90 532 123 45 67", "5321234567", seed)
            self.assertTrue(validate_phone(phone), phone)
            self.assertTrue(phone.startswith("+90 5"))
            plate = fake.like("PLATE", "34 ABC 123", "34ABC123", seed)
            self.assertTrue(validate_plate(plate), plate)
            self.assertEqual(len(plate), 10)
            self.assertTrue(validate_postal_code(fake.like("POSTAL_CODE", "34000", "34000", seed)))
        self.assertTrue(fake.like("IP", "10.1.2.3", "10.1.2.3", 1).startswith("192.0.2."))
        self.assertTrue(fake.like("IP", "fe80::1", "fe80::1", 1).startswith("2001:db8::"))
        self.assertTrue(fake.like("EMAIL", "a@b.com", "a@b.com", 1).endswith("@example.invalid"))
        self.assertEqual(fake.like("CUSTOM", "abc", "abc", 1), "[CUSTOM]")

    def test_fake_output_keeps_the_same_finding_types(self) -> None:
        text = f"TCKN {fake.tckn(seed=21)}, tel +90 532 123 45 67, IBAN {fake.tr_iban(seed=21)}"
        replaced = mask(text, style="fake", seed=1)
        self.assertEqual([m.type for m in find(text)], [m.type for m in find(replaced)])

    def test_fake_without_seed_is_random_but_valid(self) -> None:
        value = fake.tckn(seed=3)
        self.assertTrue(validate_tckn(mask(value, style="fake")))


class StatsAndCliTests(unittest.TestCase):
    def invoke(self, args: list[str], text: str = "") -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        code = main(args, stdin=io.StringIO(text), stdout=out, stderr=err)
        return code, out.getvalue(), err.getvalue()

    def test_stats_function(self) -> None:
        text = f"{fake.tckn(seed=1)} {fake.tckn(seed=2)} dummy@example.invalid"
        result = stats(find(text))
        self.assertEqual(result["total"], 3)
        self.assertEqual(result["by_type"], {"EMAIL": 1, "TCKN": 2})
        self.assertEqual(result["characters"], 11 + 11 + 21)
        self.assertEqual(stats([]), {"total": 0, "by_type": {}, "characters": 0})

    def test_scan_stats_text_and_json(self) -> None:
        text = f"{fake.tckn(seed=1)} dummy@example.invalid"
        code, out, _ = self.invoke(["scan", "-", "--stats"], text)
        self.assertEqual((code, out), (3, "total: 2\nEMAIL: 1\nTCKN: 1\n"))
        code, out, _ = self.invoke(["scan", "-", "--stats", "--format", "json"], text)
        expected = {"total": 2, "by_type": {"EMAIL": 1, "TCKN": 1}, "characters": 32}
        self.assertEqual(json.loads(out), expected)
        self.assertEqual(self.invoke(["scan", "-", "--stats"], "plain"), (0, "total: 0\n", ""))

    def test_mask_json_offsets(self) -> None:
        text = f"ağ İzin {fake.tckn(seed=1)} ve dummy@example.invalid."
        code, out, _ = self.invoke(["mask", "-", "--format", "json"], text)
        self.assertEqual(code, 3)
        data = json.loads(out)
        self.assertEqual(data["text"], mask(text))
        for finding in data["findings"]:
            self.assertEqual(
                data["text"][finding["masked_start"] : finding["masked_end"]],
                finding["replacement"],
            )
            self.assertNotEqual(text[finding["start"] : finding["end"]], finding["replacement"])
        self.assertEqual([f["type"] for f in data["findings"]], ["TCKN", "EMAIL"])

    def test_mask_fake_flag_and_seed(self) -> None:
        text = f"TCKN {fake.tckn(seed=5)}"
        a = self.invoke(["mask", "-", "--fake", "--seed", "4"], text)
        b = self.invoke(["mask", "-", "--style", "fake", "--seed", "4"], text)
        c = self.invoke(["mask", "-", "--fake", "--seed", "5"], text)
        self.assertEqual(a, b)
        self.assertNotEqual(a[1], c[1])
        self.assertEqual(a[0], 3)

    def test_mask_redact_cli(self) -> None:
        self.assertEqual(
            self.invoke(["mask", "-", "--style", "redact"], "dummy@example.invalid"),
            (3, "[REDACTED]", ""),
        )
