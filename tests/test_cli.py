import io
import string
import unittest
from contextlib import redirect_stderr, redirect_stdout
from unittest import mock

from passgen.cli import main


def run(*argv):
    out, err = io.StringIO(), io.StringIO()
    with redirect_stdout(out), redirect_stderr(err):
        code = main(list(argv))
    return code, out.getvalue(), err.getvalue()


class CliTests(unittest.TestCase):
    def test_default_run(self):
        code, out, _ = run()
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip()), 16)
        self.assertEqual(len(out.strip().splitlines()), 1)

    def test_length_flag(self):
        _, out, _ = run("-l", "32")
        self.assertEqual(len(out.strip()), 32)

    def test_count_flag(self):
        _, out, _ = run("-n", "5")
        self.assertEqual(len(out.strip().splitlines()), 5)

    def test_character_type_flags(self):
        _, out, _ = run("-l", "40", "--no-numbers", "--no-symbols")
        self.assertTrue(out.strip().isalpha())

    def test_all_types_disabled_is_an_error(self):
        code, out, err = run(
            "--no-lowercase", "--no-uppercase", "--no-numbers", "--no-symbols"
        )
        self.assertEqual(code, 2)
        self.assertEqual(out, "")
        self.assertIn("Error", err)

    def test_length_too_short_is_an_error(self):
        code, _, err = run("-l", "2")
        self.assertEqual(code, 2)
        self.assertIn("Error", err)

    def test_bad_count_is_an_error(self):
        code, _, err = run("-n", "0")
        self.assertEqual(code, 2)
        self.assertIn("Error", err)

    def test_non_numeric_length_is_rejected_by_argparse(self):
        with redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit) as ctx:
                main(["-l", "abc"])
        self.assertEqual(ctx.exception.code, 2)

    def test_entropy_goes_to_stderr(self):
        _, out, err = run("-e")
        self.assertIn("bits", err)
        self.assertNotIn("bits", out)

    def test_stdout_contains_only_the_password(self):
        _, out, _ = run("-e")
        self.assertEqual(len(out.strip().splitlines()), 1)

    @mock.patch("passgen.cli.copy_to_clipboard", return_value=True)
    def test_copy_success(self, copy):
        code, out, err = run("-c")
        self.assertEqual(code, 0)
        copy.assert_called_once_with(out.strip())
        self.assertIn("Copied", err)

    @mock.patch("passgen.cli.copy_to_clipboard", return_value=False)
    def test_copy_failure_still_prints_password(self, _copy):
        code, out, err = run("-c")
        self.assertEqual(code, 1)
        self.assertEqual(len(out.strip()), 16)
        self.assertIn("Could not copy", err)

    def test_copy_with_multiple_passwords_is_an_error(self):
        code, _, err = run("-c", "-n", "2")
        self.assertEqual(code, 2)
        self.assertIn("Error", err)

    @mock.patch("builtins.input", side_effect=["20", "y", "y", "n", "n", "n"])
    def test_interactive_mode(self, _input):
        code, out, _ = run("-i")
        self.assertEqual(code, 0)
        password = out.strip().splitlines()[-1]
        self.assertEqual(len(password), 20)
        self.assertTrue(password.isalpha())

    @mock.patch("builtins.input", side_effect=["", "", "", "", "", ""])
    def test_interactive_defaults(self, _input):
        code, out, _ = run("-i")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()[-1]), 16)

    @mock.patch("builtins.input", side_effect=["abc", "12", "maybe", "y", "y", "y", "y", ""])
    def test_interactive_retries_bad_input(self, _input):
        code, out, _ = run("-i")
        self.assertEqual(code, 0)
        self.assertEqual(len(out.strip().splitlines()[-1]), 12)

    @mock.patch("builtins.input", side_effect=KeyboardInterrupt)
    def test_interactive_ctrl_c(self, _input):
        code, _, err = run("-i")
        self.assertEqual(code, 130)
        self.assertIn("Cancelled", err)


if __name__ == "__main__":
    unittest.main()
