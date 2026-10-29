import inspect
import math
import string
import unittest

from passgen import generator
from passgen.generator import (
    AMBIGUOUS,
    MAX_LENGTH,
    SYMBOLS,
    PasswordError,
    describe_strength,
    estimate_entropy_bits,
    generate_password,
)


class GeneratePasswordTests(unittest.TestCase):
    def test_default_length_is_16(self):
        self.assertEqual(len(generate_password()), 16)

    def test_custom_lengths(self):
        for length in (4, 8, 32, 128, MAX_LENGTH):
            self.assertEqual(len(generate_password(length)), length)

    def test_every_selected_type_is_present(self):
        # Shortest possible password with all four types: no room for luck.
        for _ in range(300):
            pw = generate_password(4)
            self.assertTrue(any(c in string.ascii_lowercase for c in pw))
            self.assertTrue(any(c in string.ascii_uppercase for c in pw))
            self.assertTrue(any(c in string.digits for c in pw))
            self.assertTrue(any(c in SYMBOLS for c in pw))

    def test_lowercase_only(self):
        pw = generate_password(40, uppercase=False, numbers=False, symbols=False)
        self.assertTrue(all(c in string.ascii_lowercase for c in pw))

    def test_numbers_only(self):
        pw = generate_password(40, lowercase=False, uppercase=False, symbols=False)
        self.assertTrue(pw.isdigit())

    def test_symbols_only(self):
        pw = generate_password(40, lowercase=False, uppercase=False, numbers=False)
        self.assertTrue(all(c in SYMBOLS for c in pw))

    def test_disabled_types_never_appear(self):
        for _ in range(100):
            pw = generate_password(30, numbers=False, symbols=False)
            self.assertTrue(pw.isalpha())

    def test_exclude_ambiguous(self):
        for _ in range(100):
            pw = generate_password(64, exclude_ambiguous=True)
            self.assertFalse(any(c in AMBIGUOUS for c in pw))

    def test_too_short_for_selected_types(self):
        with self.assertRaises(PasswordError):
            generate_password(3)  # four types selected

    def test_no_types_selected(self):
        with self.assertRaises(PasswordError):
            generate_password(
                16, lowercase=False, uppercase=False, numbers=False, symbols=False
            )

    def test_invalid_lengths(self):
        for bad in (0, -5, MAX_LENGTH + 1, "12", 3.5, True, None):
            with self.subTest(length=bad):
                with self.assertRaises(PasswordError):
                    generate_password(bad)

    def test_passwords_are_not_repeated(self):
        batch = {generate_password(16) for _ in range(500)}
        self.assertEqual(len(batch), 500)

    def test_module_does_not_use_random(self):
        source = inspect.getsource(generator)
        self.assertNotIn("import random", source)
        self.assertNotIn("from random", source)


class EntropyTests(unittest.TestCase):
    def test_entropy_matches_formula(self):
        bits = estimate_entropy_bits(
            16, uppercase=False, numbers=False, symbols=False
        )
        self.assertAlmostEqual(bits, 16 * math.log2(26))

    def test_entropy_with_nothing_selected_is_zero(self):
        bits = estimate_entropy_bits(
            16, lowercase=False, uppercase=False, numbers=False, symbols=False
        )
        self.assertEqual(bits, 0.0)

    def test_strength_labels(self):
        self.assertEqual(describe_strength(20), "weak")
        self.assertEqual(describe_strength(50), "fair")
        self.assertEqual(describe_strength(70), "good")
        self.assertEqual(describe_strength(90), "strong")
        self.assertEqual(describe_strength(120), "very strong")


if __name__ == "__main__":
    unittest.main()
