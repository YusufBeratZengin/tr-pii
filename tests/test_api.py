import unittest
from dataclasses import FrozenInstanceError

from tr_pii import Match, fake, find, mask

from .test_validators import grouped


class DetectionTests(unittest.TestCase):
    def test_offsets_after_turkish_and_astral_characters(self) -> None:
        value = fake.tckn(seed=4)
        text = "İçerik 𐀀: " + value + "; bitti."
        match = find(text, ["TCKN"])[0]
        self.assertEqual(match.start, text.index(value))
        self.assertEqual(text[match.start : match.end], value)
        self.assertEqual(match.confidence, 0.99)
        with self.assertRaises(FrozenInstanceError):
            match.start = 0  # type: ignore[misc]

    def test_numeric_boundaries_and_false_positives(self) -> None:
        for value in (fake.tckn(seed=6), fake.vkn(seed=6), fake.credit_card(seed=6)):
            for wrapped in ("SKU" + value, value + "X", "ş" + value + "ü", "9" + value + "9"):
                self.assertEqual(find(wrapped), [])
        for text in (
            "Fatura INV-2026-007; tarih 22.10.2026; ürün SKU-AB12345.",
            "Miktar 81007, fiyat 123.45, sürüm 1.2.3.",
            "",
            "Normal Türkçe metin.",
        ):
            self.assertEqual(find(text), [])
        card = grouped(fake.credit_card(seed=23))
        self.assertEqual(find("7 " + card + " 8", ["CREDIT_CARD"]), [])

    def test_unlabelled_phone_vkn_and_common_non_pii_false_positives(self) -> None:
        from tr_pii import validate_tckn, validate_vkn

        # Invoice numbers (standard alphanumeric and numeric non-VKN checksum)
        inv1 = "Fatura No: INV-2026-00042"
        inv2 = "Fatura No: GIB2026000000042"
        non_vkn = next(
            f"{n:010d}" for n in range(1000000000, 1000000100) if not validate_vkn(f"{n:010d}")
        )
        inv3 = f"Fatura No: {non_vkn}"
        for inv in (inv1, inv2, inv3):
            self.assertEqual(find(inv), [])

        # ISO dates
        self.assertEqual(find("2026-10-22"), [])
        self.assertEqual(find("Sözleşme tarihi: 2026-10-22."), [])

        # Product codes
        self.assertEqual(find("TR-1234-5678"), [])
        self.assertEqual(find("Ürün Kodu: TR-1234-5678"), [])

        # 11-digit order numbers failing TCKN checksum
        non_tckn = next(
            f"{n:011d}" for n in range(10000000000, 10000000100) if not validate_tckn(f"{n:011d}")
        )
        self.assertEqual(find(f"Sipariş No: {non_tckn}"), [])

        # Labelled national phone cases (explicit context detects bare 10 digits)
        for label in ("Tel:", "GSM:", "Telefon:", "Cep:"):
            matches = find(f"{label} 5321234567")
            self.assertEqual(len(matches), 1)
            self.assertEqual(matches[0].type, "PHONE")
            self.assertEqual(matches[0].value, "5321234567")

        # Unlabelled bare 10-digit national phone (avoids false-positive on bare digits)
        self.assertEqual(find("5321234567", ["PHONE"]), [])

        # Bare 10-digit checksum-valid VKN
        valid_vkn = fake.vkn(seed=10)
        vkn_matches = find(valid_vkn, ["VKN"])
        self.assertEqual(len(vkn_matches), 1)
        self.assertEqual(vkn_matches[0].type, "VKN")
        self.assertEqual(vkn_matches[0].value, valid_vkn)

    def test_overlaps_checksum_confidence_and_longest(self) -> None:
        # A phone can also pass the one-digit VKN checksum. Context wins.
        from tr_pii import validate_vkn

        national = next("532" + f"{n:07d}" for n in range(100) if validate_vkn("532" + f"{n:07d}"))
        self.assertEqual([m.type for m in find("Telefon: " + national)], ["PHONE"])
        value = fake.tr_iban(seed=19)
        self.assertEqual([m.type for m in find(grouped(value))], ["IBAN"])
        text = "Sahte Terim Uzun"
        matches = find(text, custom_terms=["Sahte Terim", text, "Terim Uzun"])
        self.assertEqual([m.value for m in matches], [text])

    def test_custom_turkish_case_boundaries_and_offsets(self) -> None:
        text = "İZİN izin IZIN ızın; IŞIK ışık İŞİK işik; izinli."
        matches = find(text, custom_terms=["izin", "ışık", "İZİN"])
        self.assertEqual([m.value for m in matches], ["İZİN", "izin", "IŞIK", "ışık"])
        for match in matches:
            self.assertEqual(text[match.start : match.end], match.value)
        self.assertEqual(find("Sahte Terim"), [])
        self.assertEqual(len(find("ÖZEL Terim", custom_terms=["özel terim"])), 1)
        self.assertEqual(len(find("a+b", custom_terms=["a+b"])), 1)
        with self.assertRaises(ValueError):
            find("text", custom_terms=[" "])
        with self.assertRaises(ValueError):
            find("text", custom_terms="text")

    def test_type_selection_and_invalid_type(self) -> None:
        text = "dummy@example.invalid; " + fake.tckn(seed=8)
        self.assertEqual([m.type for m in find(text, ["email"])], ["EMAIL"])
        self.assertEqual(find(text, []), [])
        self.assertEqual(find(text, iter(["EMAIL"])), find(text, ["EMAIL"]))
        with self.assertRaisesRegex(ValueError, "Unknown PII types"):
            find(text, ["UNKNOWN"])
        with self.assertRaises(ValueError):
            find(text, "EMAIL")

    def test_source_order_and_adjacent_matches(self) -> None:
        text = fake.tckn(seed=2) + ";dummy@example.invalid;" + fake.tr_iban(seed=8)
        matches = find(text)
        self.assertEqual([m.type for m in matches], ["TCKN", "EMAIL", "IBAN"])
        self.assertTrue(all(a.end <= b.start for a, b in zip(matches, matches[1:], strict=False)))


class MaskingTests(unittest.TestCase):
    def test_tags_stars_and_partial(self) -> None:
        value = fake.tckn(seed=9)
        text = "Önce " + value + " sonra"
        self.assertEqual(mask(text), "Önce [TCKN] sonra")
        self.assertEqual(mask(text, "stars"), "Önce " + "*" * 11 + " sonra")
        self.assertEqual(mask(text, "partial"), "Önce " + "*" * 9 + value[-2:] + " sonra")
        for kind, number in (
            ("IBAN", fake.tr_iban(seed=9)),
            ("CREDIT_CARD", fake.credit_card(seed=9)),
        ):
            result = mask(number, "partial", [kind])
            self.assertEqual(result[-4:], number[-4:])
            self.assertEqual(result[:-4], "*" * (len(number) - 4))
        self.assertEqual(mask("dummy@example.invalid", "partial"), "*" * 21)
        self.assertEqual(mask("Sahte Terim", "partial", custom_terms=["Sahte Terim"]), "*" * 11)
        self.assertEqual(mask("plain", types=[]), "plain")

    def test_hash_normalization_salt_and_stability(self) -> None:
        value = fake.tr_iban(seed=1)
        first = mask(value, "hash", salt="public-test-salt")
        self.assertEqual(first, mask(grouped(value).lower(), "hash", salt="public-test-salt"))
        self.assertNotEqual(first, mask(value, "hash", salt="another-public-test-salt"))
        self.assertRegex(first, r"^\[IBAN:[a-f0-9]{16}\]$")
        self.assertEqual(
            mask(value + ";" + value, "hash", salt="public-test-salt"), first + ";" + first
        )

    def test_numeric_email_is_masked_as_one_finding(self) -> None:
        text = fake.tckn(seed=63) + "@example.invalid"
        self.assertEqual([match.type for match in find(text)], ["EMAIL"])
        self.assertEqual(mask(text), "[EMAIL]")

    def test_invalid_masking_options(self) -> None:
        for salt in (None, ""):
            with self.assertRaisesRegex(ValueError, "non-empty salt"):
                mask("plain", "hash", salt=salt)
        with self.assertRaisesRegex(ValueError, "style must"):
            mask("plain", "wrong")  # type: ignore[arg-type]

    def test_hash_phone_ip_and_custom_normalization(self) -> None:
        national = "532" + "0" * 6 + "7"
        self.assertEqual(
            mask("0" + national, "hash", ["PHONE"], "public-test-salt"),
            mask("+90 " + national, "hash", ["PHONE"], "public-test-salt"),
        )
        self.assertEqual(
            mask("2001:db8::7", "hash", salt="public-test-salt"),
            mask("2001:0db8:0:0:0:0:0:7", "hash", salt="public-test-salt"),
        )
        self.assertEqual(
            mask("İZİN", "hash", salt="public-test-salt", custom_terms=["izin"]),
            mask("izin", "hash", salt="public-test-salt", custom_terms=["izin"]),
        )

    def test_partial_each_numeric_family_and_star_length(self) -> None:
        samples = (
            ("VKN", fake.vkn(seed=87), 2),
            ("PHONE", "+90 (532) " + "0" * 3 + "-" + "0" * 2 + "-07", 4),
            ("POSTAL_CODE", "PK: " + "81" + "0" * 2 + "7", 2),
            ("PLATE", "81 ZZ " + "0" * 2 + "7", 2),
        )
        for kind, text, count in samples:
            with self.subTest(kind=kind):
                match = find(text, [kind])[0]
                original_digits = "".join(
                    char for char in match.value if char.isascii() and char.isdigit()
                )
                partial = mask(match.value, "partial", [kind])
                if kind == "POSTAL_CODE":
                    partial = mask(text, "partial", [kind])[match.start :]
                visible = "".join(char for char in partial if char != "*")
                self.assertEqual(visible, original_digits[-count:])
                self.assertEqual(len(mask(text, "stars", [kind])), len(text))

    def test_match_model(self) -> None:
        self.assertEqual(Match("EMAIL", 0, 1, "x", 0.5).value, "x")


if __name__ == "__main__":
    unittest.main()
