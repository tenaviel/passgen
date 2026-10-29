import string
import unittest

from passgen import gui
from passgen.generator import SYMBOLS, PasswordError


class MakePasswordTests(unittest.TestCase):
    """These don't need a window, so they run everywhere."""

    def test_default_settings(self):
        password, bits, label = gui.make_password(16, True, True, True, True, False)
        self.assertEqual(len(password), 16)
        self.assertGreater(bits, 100)
        self.assertEqual(label, "very strong")

    def test_options_are_respected(self):
        password, _, _ = gui.make_password(40, True, False, False, False, False)
        self.assertTrue(all(c in string.ascii_lowercase for c in password))

    def test_ambiguous_characters_are_avoided(self):
        for _ in range(50):
            password, _, _ = gui.make_password(40, True, True, True, True, True)
            self.assertFalse(any(c in "il1Lo0O" for c in password))

    def test_no_character_types_raises(self):
        with self.assertRaises(PasswordError):
            gui.make_password(16, False, False, False, False, False)

    def test_guide_mentions_clipboard_timeout(self):
        self.assertIn(str(gui.CLIPBOARD_CLEAR_SECONDS), gui.GUIDE_TEXT)


@unittest.skipIf(gui.tk is None, "tkinter is not installed")
class WindowTests(unittest.TestCase):
    """Build the real window, hidden. Skipped when there is no display."""

    def setUp(self):
        try:
            self.root = gui.tk.Tk()
        except gui.tk.TclError:
            self.skipTest("no display available")
        self.root.withdraw()
        self.addCleanup(self.root.destroy)
        self.app = gui.PassgenApp(self.root)

    def test_password_is_ready_on_start(self):
        self.assertEqual(len(self.app.password.get()), gui.DEFAULT_LENGTH)

    def test_changing_length(self):
        self.app.length.set(30)
        self.app.generate()
        self.assertEqual(len(self.app.password.get()), 30)

    def test_unticking_boxes(self):
        self.app.numbers.set(False)
        self.app.symbols.set(False)
        self.app.generate()
        self.assertTrue(self.app.password.get().isalpha())

    def test_symbols_only(self):
        self.app.lowercase.set(False)
        self.app.uppercase.set(False)
        self.app.numbers.set(False)
        self.app.generate()
        self.assertTrue(all(c in SYMBOLS for c in self.app.password.get()))

    def test_nothing_selected_shows_an_error(self):
        for var in (self.app.lowercase, self.app.uppercase,
                    self.app.numbers, self.app.symbols):
            var.set(False)
        self.app.generate()
        self.assertEqual(self.app.password.get(), "")
        self.assertIn("at least one", self.app.status.get())

    def test_new_password_each_time(self):
        seen = set()
        for _ in range(20):
            self.app.generate()
            seen.add(self.app.password.get())
        self.assertEqual(len(seen), 20)


if __name__ == "__main__":
    unittest.main()
