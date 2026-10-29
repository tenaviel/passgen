import subprocess
import unittest
from unittest import mock

from passgen import clipboard


class ClipboardTests(unittest.TestCase):
    @mock.patch("passgen.clipboard._candidate_commands", return_value=[["fakeclip"]])
    @mock.patch("passgen.clipboard.shutil.which", return_value="/usr/bin/fakeclip")
    @mock.patch("passgen.clipboard.subprocess.run")
    def test_success(self, run, _which, _cmds):
        self.assertTrue(clipboard.copy_to_clipboard("secret"))
        self.assertEqual(run.call_args.kwargs["input"], b"secret")

    @mock.patch("passgen.clipboard._candidate_commands", return_value=[["fakeclip"]])
    @mock.patch("passgen.clipboard.shutil.which", return_value=None)
    def test_no_tool_installed(self, _which, _cmds):
        self.assertFalse(clipboard.copy_to_clipboard("secret"))

    @mock.patch("passgen.clipboard._candidate_commands", return_value=[["fakeclip"]])
    @mock.patch("passgen.clipboard.shutil.which", return_value="/usr/bin/fakeclip")
    @mock.patch(
        "passgen.clipboard.subprocess.run",
        side_effect=subprocess.CalledProcessError(1, "fakeclip"),
    )
    def test_tool_fails(self, _run, _which, _cmds):
        self.assertFalse(clipboard.copy_to_clipboard("secret"))

    @mock.patch(
        "passgen.clipboard._candidate_commands",
        return_value=[["broken"], ["working"]],
    )
    @mock.patch("passgen.clipboard.shutil.which", return_value="/usr/bin/x")
    @mock.patch("passgen.clipboard.subprocess.run", side_effect=[OSError, None])
    def test_falls_back_to_next_tool(self, run, _which, _cmds):
        self.assertTrue(clipboard.copy_to_clipboard("secret"))
        self.assertEqual(run.call_count, 2)


if __name__ == "__main__":
    unittest.main()
