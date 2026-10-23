"""Generated fixtures and independent checksum oracles; no real identity data."""

import io
import json
import random
import unittest

from tr_pii import Style, fake, find, mask, validate_mersis, validate_passport, validate_tr_iban
from tr_pii.vkn import check_digit, validate_vkn

from .test_validators import corrupt, grouped


def reference_vkn(prefix: str) -> str:
    """Use decimal digital roots instead of the production modulo-9 shortcut."""
    total = 0
    for position, digit in enumerate(prefix, start=1):
        product = ((int(digit) + 10 - position) % 10) * 2 ** (10 - position)
        while product > 9:
            product = sum(map(int, str(product)))
        total += product
    return prefix + str((10 - total % 10) % 10)


def reference_iban(bban: str) -> str:
    """TR expands to 2927; use an integer oracle independent of mod97()."""
    return f"TR{98 - int(bban + '292700') % 97:02d}" + bban


class IdentifierRegressionTests(unittest.TestCase):
    def test_vkn_reference_and_all_check_digit_mutations(self) -> None:
        rng = random.Random(20261024)
        # These exercise adjusted-zero and nonzero-multiple-of-nine branches.
        prefixes = ["123456789", "012345678", "0" * 9]
        prefixes += ["".join(str(rng.randrange(10)) for _ in range(9)) for _ in range(100)]
        for prefix in prefixes:
            value = reference_vkn(prefix)
            with self.subTest(prefix=prefix):
                self.assertEqual(check_digit(prefix), value[-1])
                self.assertTrue(validate_vkn(value))
                self.assertEqual([m.value for m in find(value, ["VKN"])], [value])
                for digit in "0123456789":
                    if digit != value[-1]:
                        wrong = prefix + digit
                        self.assertFalse(validate_vkn(wrong))
                        self.assertEqual(find(wrong, ["VKN"]), [])

    def test_vkn_format_and_token_boundaries(self) -> None:
        value = fake.vkn(seed=73)
        for invalid in ("", value[:-1], value + "0", "１" + value[1:], value[:4] + " " + value[4:]):
            with self.subTest(invalid=invalid):
                self.assertFalse(validate_vkn(invalid))
                self.assertEqual(find(invalid, ["VKN"]), [])
        for text in ("SKU" + value, value + "X", "_" + value, "ş" + value, value + "ü"):
            self.assertEqual(find(text, ["VKN"]), [])

    def test_iban_independent_generation_and_single_digit_errors(self) -> None:
        rng = random.Random(97)
        for _ in range(30):
            bban = "0" * 6 + "".join(str(rng.randrange(10)) for _ in range(16))
            value = reference_iban(bban)
            self.assertTrue(validate_tr_iban(value))
            for separator in (" ", "\t", "\u00a0"):
                formatted = grouped(value).replace(" ", separator).lower()
                self.assertTrue(validate_tr_iban(formatted))
                self.assertEqual([m.value for m in find(formatted, ["IBAN"])], [formatted])
            for index in range(2, len(value)):
                wrong = value[:index] + str((int(value[index]) + 1) % 10) + value[index + 1 :]
                self.assertFalse(validate_tr_iban(wrong))
                self.assertEqual(find(wrong, ["IBAN"]), [])

    def test_iban_shape_reserved_digit_and_boundaries(self) -> None:
        value = fake.tr_iban(seed=73)
        for wrong in (
            value[:-1],
            value + "0",
            value.replace("TR", "DE"),
            value[:4] + "０" + value[5:],
            reference_iban("0" * 5 + "1" + "0" * 16),
            value[:8] + "\n" + value[8:],
        ):
            self.assertFalse(validate_tr_iban(wrong))
            self.assertEqual(find(wrong, ["IBAN"]), [])
        for text in ("SKU" + value, value + "X", "_" + value, "ş" + value):
            self.assertEqual(find(text, ["IBAN"]), [])

    def test_passport_labels_lengths_case_and_offsets(self) -> None:
        generated = fake.passport(seed=73)
        for value in (generated, generated[:-1]):
            self.assertTrue(validate_passport(value))
            for label in ("Pasaport", "PASAPORT NO.", "pasaport numarası", "passport number"):
                text = f"İçerik 😀 {label}: {value.lower()}; son."
                matches = find(text, ["PASSPORT"])
                self.assertEqual(len(matches), 1)
                self.assertEqual(text[matches[0].start : matches[0].end], value.lower())
        for wrong in (generated[:1] + "１２３４５６７８", generated[1:], generated + "0"):
            self.assertFalse(validate_passport(wrong))
            self.assertEqual(find("Pasaport: " + wrong, ["PASSPORT"]), [])
        for text in (
            generated,
            "Ürün: " + generated,
            "pasaport" + generated,
            "epasaport: " + generated,
            "passport: SKU" + generated,
            "pasaport: " + generated + "X",
            "passport numbers: " + generated,
        ):
            self.assertEqual(find(text, ["PASSPORT"]), [])

    def test_mersis_labels_layout_leading_zero_and_false_positives(self) -> None:
        value = "0" + fake.mersis(seed=73)[1:]
        self.assertTrue(validate_mersis(value))
        for label in ("MERSİS", "mersis no.", "MERSIS NUMARASI", "Mersis numarası"):
            for formatted in (value, grouped(value), grouped(value).replace(" ", "-")):
                self.assertTrue(validate_mersis(formatted))
                text = f"İçerik 😀 {label}: {formatted}; son."
                matches = find(text, ["MERSIS"])
                self.assertEqual([m.value for m in matches], [formatted])
                self.assertEqual(text[matches[0].start : matches[0].end], formatted)
        for wrong in (value[:-1], value + "0", "０" + value[1:], value[:8] + "X" + value[9:]):
            self.assertFalse(validate_mersis(wrong))
            self.assertEqual(find("MERSİS: " + wrong, ["MERSIS"]), [])
        for text in (value, "Sipariş: " + value, "MERSIS" + value, "XMERSIS: " + value):
            self.assertEqual(find(text, ["MERSIS"]), [])


class StrategyRegressionTests(unittest.TestCase):
    def test_full_and_last_four_for_all_requested_identifiers(self) -> None:
        for kind, value, label in (
            ("VKN", fake.vkn(seed=73), "VKN"),
            ("IBAN", grouped(fake.tr_iban(seed=73)), "IBAN"),
            ("PASSPORT", fake.passport(seed=73), "Pasaport"),
            ("MERSIS", grouped(fake.mersis(seed=73)).replace(" ", "-"), "MERSİS"),
        ):
            text = f"{label}: {value}; bitti"
            with self.subTest(kind=kind):
                self.assertEqual(mask(text, "stars", [kind]), f"{label}: {'*' * len(value)}; bitti")
                partial = mask(text, "last4", [kind])
                self.assertTrue(partial.startswith(f"{label}: "))
                self.assertTrue(partial.endswith("; bitti"))
                replacement = partial[len(label) + 2 : -7]
                self.assertEqual(len(replacement), len(value))
                self.assertEqual(replacement.count("*"), len(value) - 4)
                self.assertEqual(
                    replacement.replace("*", ""), "".join(c for c in value if c.isdigit())[-4:]
                )
                self.assertEqual(mask(text, "placeholder", [kind]), f"{label}: [{kind}_1]; bitti")
                self.assertEqual(
                    mask(text, "hash", [kind], "public-test-salt"),
                    mask(text, "hash", [kind], "public-test-salt"),
                )
                self.assertNotIn(value, mask(text, "hash", [kind], "public-test-salt"))
                self.assertNotEqual(
                    mask(text, "hash", [kind], "public-test-salt"),
                    mask(text, "hash", [kind], "other-public-test-salt"),
                )

    def test_last4_does_not_reveal_email_ip_or_dictionary_fragments(self) -> None:
        for text, terms in (
            ("dummy@example.invalid", ()),
            ("192.0.2.7", ()),
            ("Özel Terim", ("özel terim",)),
        ):
            self.assertEqual(mask(text, "last4", custom_terms=terms), "*" * len(text))

    def test_placeholder_reuses_canonical_values_and_counts_per_type(self) -> None:
        one, two = fake.tr_iban(seed=1), fake.tr_iban(seed=2)
        text = f"{one}; dummy@example.invalid; {two}; {grouped(one).lower()}"
        expected = "[IBAN_1]; [EMAIL_1]; [IBAN_2]; [IBAN_1]"
        self.assertEqual(mask(text, "placeholder"), expected)
        self.assertEqual(mask(text, "placeholder"), expected)
        self.assertEqual(mask(two, "placeholder"), "[IBAN_1]")
        self.assertEqual(
            mask(text, "placeholder", ["EMAIL"]), f"{one}; [EMAIL_1]; {two}; {grouped(one).lower()}"
        )
        self.assertEqual(mask("plain", "placeholder"), "plain")
        self.assertEqual(
            mask("İZİN izin", "placeholder", custom_terms=["izin"]), "[CUSTOM_1] [CUSTOM_1]"
        )

    def test_hash_canonical_passport_and_mersis(self) -> None:
        passport = fake.passport(seed=73)
        mersis = fake.mersis(seed=73)
        for original, equivalent, kind in (
            (f"Pasaport: {passport}", f"Pasaport: {passport.lower()}", "PASSPORT"),
            (f"MERSİS: {mersis}", f"MERSİS: {grouped(mersis)}", "MERSIS"),
        ):
            self.assertEqual(
                mask(original, "hash", [kind], "public-test-salt"),
                mask(equivalent, "hash", [kind], "public-test-salt"),
            )

    def test_invalid_identifiers_remain_unchanged_in_each_strategy(self) -> None:
        text = f"VKN: {corrupt(fake.vkn(seed=73))}; IBAN: {corrupt(fake.tr_iban(seed=73))}"
        styles: tuple[Style, ...] = ("stars", "last4", "hash", "placeholder")
        for style in styles:
            self.assertEqual(mask(text, style, ["VKN", "IBAN"], "public-test-salt"), text)

    def test_cli_new_styles_and_json_offsets(self) -> None:
        from tr_pii.cli import main

        value = fake.tr_iban(seed=73)
        text = f"😀 {value}; {value}; {fake.vkn(seed=73)}"
        styles: tuple[Style, ...] = ("last4", "placeholder")
        for style in styles:
            out, err = io.StringIO(), io.StringIO()
            code = main(
                ["mask", "-", "--style", style, "--format", "json"],
                stdin=io.StringIO(text),
                stdout=out,
                stderr=err,
            )
            self.assertEqual((code, err.getvalue()), (3, ""))
            data = json.loads(out.getvalue())
            self.assertEqual(data["text"], mask(text, style))
            for match in data["findings"]:
                self.assertEqual(
                    data["text"][match["masked_start"] : match["masked_end"]], match["replacement"]
                )
