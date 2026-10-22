"""All checksum fixtures are generated, never copied from real identifiers."""

import unittest
from collections.abc import Callable

from tr_pii import (
    fake,
    find,
    validate_credit_card,
    validate_custom_term,
    validate_email,
    validate_iban,
    validate_ip,
    validate_phone,
    validate_plate,
    validate_postal_code,
    validate_tckn,
    validate_tr_iban,
    validate_vkn,
)
from tr_pii.iban import mod97
from tr_pii.vkn import check_digit


def corrupt(value: str) -> str:
    return value[:-1] + str((int(value[-1]) + 1) % 10)


def grouped(value: str, size: int = 4) -> str:
    return " ".join(value[i : i + size] for i in range(0, len(value), size))


def foreign_iban(country: str, bban: str) -> str:
    return country + f"{98 - mod97(bban + country + '00'):02d}" + bban


class ChecksumTests(unittest.TestCase):
    def test_generated_values_and_corruption(self) -> None:
        cases: list[tuple[str, Callable[..., str], Callable[[str], bool]]] = [
            ("TCKN", fake.tckn, validate_tckn),
            ("VKN", fake.vkn, validate_vkn),
            ("IBAN", fake.tr_iban, validate_tr_iban),
            ("CREDIT_CARD", fake.credit_card, validate_credit_card),
        ]
        for kind, factory, validator in cases:
            for seed in range(100):
                with self.subTest(kind=kind, seed=seed):
                    value = factory(seed=seed)
                    self.assertTrue(validator(value))
                    self.assertFalse(validator(corrupt(value)))
                    self.assertEqual([m.type for m in find(value, [kind])], [kind])
                    self.assertEqual(find(corrupt(value), [kind]), [])

    def test_tckn_both_checks_and_first_digit(self) -> None:
        value = fake.tckn(seed=21)
        wrong_tenth = value[:9] + str((int(value[9]) + 1) % 10)
        wrong_tenth += str(sum(map(int, wrong_tenth)) % 10)
        self.assertFalse(validate_tckn(wrong_tenth))
        self.assertFalse(validate_tckn("0" + value[1:]))
        self.assertFalse(validate_tckn(value[:-1]))
        self.assertFalse(validate_tckn("１" + value[1:]))
        for sep in (" ", ".", "\u00a0"):
            formatted = sep.join((value[:3], value[3:6], value[6:9], value[9:]))
            self.assertTrue(validate_tckn(formatted))
            self.assertEqual(find(formatted, ["TCKN"])[0].value, formatted)
        mixed = " ".join((value[:3], value[3:6])) + "." + value[6:9] + " " + value[9:]
        self.assertFalse(validate_tckn(mixed))

    def test_vkn_independent_digit_table(self) -> None:
        # Hand-derived residues for nine zero digits, from powers 2**9 ... 2**1.
        residues = [9, 5, 5, 6, 7, 1, 6, 8, 2]
        self.assertEqual(check_digit("0" * 9), str(-sum(residues) % 10))
        value = "0" * 9 + str(-sum(residues) % 10)
        self.assertTrue(validate_vkn(value))
        self.assertFalse(validate_vkn(value + "0"))
        self.assertFalse(validate_vkn("x" + value[1:]))
        self.assertFalse(validate_vkn(""))
        with self.assertRaisesRegex(ValueError, "9 ASCII digits"):
            check_digit("bad")

    def test_iban_formats_country_length_and_mod97(self) -> None:
        value = fake.tr_iban(seed=32)
        self.assertTrue(validate_iban(grouped(value).lower()))
        self.assertEqual(len(find(grouped(value), ["IBAN"])), 1)
        german = foreign_iban("DE", "0" * 17 + "7")
        british = foreign_iban("GB", "TEST" + "0" * 13 + "7")
        for foreign in (german, british):
            self.assertTrue(validate_iban(foreign))
            self.assertFalse(validate_tr_iban(foreign))
            self.assertEqual(find(foreign, ["IBAN"]), [])
        self.assertFalse(validate_iban(foreign_iban("ZZ", "0" * 18)))
        self.assertFalse(validate_iban(foreign_iban("DE", "0" * 17)))
        self.assertFalse(validate_iban(foreign_iban("TR", "0" * 5 + "1" + "0" * 16)))
        self.assertFalse(validate_iban(foreign_iban("TR", "0" * 6 + "A" * 16)))
        self.assertFalse(validate_iban("TR00" + value[4:]))
        self.assertFalse(validate_iban("TR99" + value[4:]))
        self.assertFalse(validate_iban(value.replace("0", "０", 1)))
        self.assertFalse(validate_iban(value + "!"))

    def test_iban_independent_integer_remainder(self) -> None:
        value = fake.tr_iban(seed=45)
        reordered = value[4:] + value[:4]
        expanded = "".join(
            char if char.isdigit() else str(ord(char) - ord("A") + 10) for char in reordered
        )
        self.assertEqual(int(expanded) % 97, 1)

    def test_luhn_lengths_separators_and_degenerate_values(self) -> None:
        for length in range(13, 20):
            value = fake.credit_card(length=length, seed=length)
            self.assertTrue(validate_credit_card(value))
            self.assertTrue(validate_credit_card(grouped(value)))
            self.assertTrue(validate_credit_card(grouped(value).replace(" ", "-")))
            self.assertFalse(validate_credit_card(corrupt(value)))
        for invalid in ("0" * 16, "1" * 12, "1" * 20, "999x" + "0" * 12, ""):
            self.assertFalse(validate_credit_card(invalid))
        # Independent hand-derived check digits for odd/even total lengths.
        self.assertTrue(validate_credit_card("1" + "0" * 11 + "9"))
        self.assertTrue(validate_credit_card("1" + "0" * 14 + "8"))

    def test_fake_repeatability_and_bad_arguments(self) -> None:
        self.assertEqual(fake.tckn(seed=5), fake.tckn(seed=5))
        self.assertNotEqual(fake.tckn(seed=5), fake.tckn(seed=6))
        for length in (0, 12, 20):
            with self.assertRaises(ValueError):
                fake.credit_card(length=length)
        for prefix in ("", "x", "1" * 16):
            with self.assertRaises(ValueError):
                fake.credit_card(prefix=prefix)


class FormatTests(unittest.TestCase):
    def test_phone_variants(self) -> None:
        # Synthetic subscriber suffixes only; no numbers are contacted.
        mobile = "5" + "32" + "0" * 6 + "7"
        fixed = "2" + "12" + "0" * 6 + "7"
        for national in (mobile, fixed):
            for prefix in ("+90 ", "0090", "0", ""):
                for shape in (
                    national,
                    f"{national[:3]} {national[3:6]} {national[6:8]} {national[8:]}",
                    f"({national[:3]}) {national[3:6]}-{national[6:8]}-{national[8:]}",
                ):
                    with self.subTest(prefix=prefix, shape=shape):
                        self.assertTrue(validate_phone(prefix + shape))
                        found = find(prefix + shape, ["PHONE"])
                        self.assertEqual(len(found), int(bool(prefix or shape != national)))
            self.assertEqual(len(find("Telefon: " + national, ["PHONE"])), 1)
        for invalid in ("+1" + mobile, "0999" + "0" * 7, mobile[:-1], "0(" + mobile):
            self.assertFalse(validate_phone(invalid))
        self.assertEqual(find("Fatura no: " + mobile, ["PHONE"]), [])

    def test_email(self) -> None:
        for value in (
            "dummy@example.invalid",
            "test+label@sub.example.invalid",
            "x.y@example.invalid",
        ):
            self.assertTrue(validate_email(value))
            self.assertEqual(len(find(value, ["EMAIL"])), 1)
        for invalid in (
            "a..b@example.invalid",
            ".dummy@example.invalid",
            "x@-example.invalid",
            "x@example",
            "x@exam_ple.invalid",
            "x" * 65 + "@example.invalid",
            "",
        ):
            self.assertFalse(validate_email(invalid))
            self.assertEqual(find(invalid, ["EMAIL"]), [])
        self.assertFalse(validate_email("örnek@example.invalid"))
        self.assertEqual(find("örnek@example.invalid", ["EMAIL"]), [])

    def test_plate_combinations(self) -> None:
        for letters, count in (("Z", 4), ("ZZ", 3), ("ZZ", 4), ("ZZZ", 2), ("ZZZ", 3)):
            for province in ("01", "81"):
                value = province + " " + letters + " " + "0" * (count - 1) + "7"
                compact = value.replace(" ", "")
                for formatted in (value, compact, compact.lower()):
                    self.assertTrue(validate_plate(formatted))
                    self.assertEqual(len(find(formatted, ["PLATE"])), 1)
                lowered = value.lower()
                self.assertFalse(validate_plate(lowered))
                self.assertEqual(find(lowered, ["PLATE"]), [])
        for invalid in (
            "00 ZZ 007",
            "82 ZZ 007",
            "01 Q 0007",
            "01 W 0007",
            "01 X 0007",
            "01 İ 0007",
            "01 Z 07",
            "01 ZZ 07",
            "01 ZZZ 0007",
            "01 ZZZZ 07",
        ):
            self.assertFalse(validate_plate(invalid))
            self.assertEqual(find(invalid, ["PLATE"]), [])
        self.assertEqual(find("ş01ZZ007ü", ["PLATE"]), [])

    def test_plate_lowercase_spaced_is_not_plate(self) -> None:
        for text in ("42 at 100", "34 km 120", "06 da 1234", "34 km  120", "06 Da 1234"):
            self.assertFalse(validate_plate(text))
            self.assertEqual(find("hız " + text + " idi", ["PLATE"]), [])
        self.assertEqual(len(find("araç 34 ABC 123 geçti", ["PLATE"])), 1)

    def test_ip_addresses(self) -> None:
        # RFC documentation networks, unspecified and loopback addresses.
        valid = ("192.0.2.7", "2001:db8::7", "::1", "::", "::ffff:192.0.2.7")
        for value in valid:
            self.assertTrue(validate_ip(value))
            self.assertEqual([m.value for m in find(value, ["IP"])], [value])
            self.assertEqual([m.value for m in find("IP [" + value + "].", ["IP"])], [value])
        for invalid in (
            "256.0.2.7",
            "192.00.2.7",
            "2001:db8:::7",
            "1:2:3:4:5:6:7:8:9",
            "::gg",
            "192.0.2.7/24",
            "fe80::1%test",
            "",
        ):
            self.assertFalse(validate_ip(invalid))
        for invalid in ("256.0.2.7", "192.00.2.7", "2001:db8:::7", "::gg", "x192.0.2.7y"):
            self.assertEqual(find(invalid, ["IP"]), [])
        self.assertEqual([m.value for m in find("192.0.2.7.", ["IP"])], ["192.0.2.7"])

    def test_contextual_postal_codes(self) -> None:
        value = "81" + "0" * 2 + "7"
        self.assertTrue(validate_postal_code(value))
        self.assertEqual(find(value, ["POSTAL_CODE"]), [])
        for label in ("posta kodu", "POSTA KODU:", "PK", "pk."):
            found = find(label + " " + value, ["POSTAL_CODE"])
            self.assertEqual([m.value for m in found], [value])
        for invalid in ("00007", "82007", "8107", "810007", "８１００７", ""):
            self.assertFalse(validate_postal_code(invalid))
            self.assertEqual(find("PK " + invalid, ["POSTAL_CODE"]), [])
        self.assertEqual(find("ürünPK " + value, ["POSTAL_CODE"]), [])

    def test_custom_validator_turkish_case(self) -> None:
        self.assertTrue(validate_custom_term("İZİN", "izin"))
        self.assertTrue(validate_custom_term("IŞIK", "ışık"))
        self.assertFalse(validate_custom_term("IZIN", "izin"))
        self.assertFalse(validate_custom_term("İŞİK", "ışık"))
        self.assertFalse(validate_custom_term("", ""))


if __name__ == "__main__":
    unittest.main()
