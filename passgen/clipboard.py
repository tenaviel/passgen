"""Copy text to the system clipboard without any third-party packages.

This works by calling the clipboard tool your operating system already has.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from typing import List


def _candidate_commands() -> List[List[str]]:
    """Clipboard commands to try, in order, for the current platform."""
    if sys.platform == "darwin":
        return [["pbcopy"]]
    if sys.platform.startswith("win"):
        return [["clip"]]
    # Linux / BSD (Wayland first, then X11), plus clip.exe for WSL.
    return [
        ["wl-copy"],
        ["xclip", "-selection", "clipboard"],
        ["xsel", "--clipboard", "--input"],
        ["clip.exe"],
    ]


def copy_to_clipboard(text: str) -> bool:
    """Copy ``text`` to the clipboard. Returns True on success, False otherwise."""
    for command in _candidate_commands():
        if shutil.which(command[0]) is None:
            continue
        try:
            subprocess.run(
                command,
                input=text.encode("utf-8"),
                check=True,
                timeout=5,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
            return True
        except (subprocess.SubprocessError, OSError):
            continue
    return False
