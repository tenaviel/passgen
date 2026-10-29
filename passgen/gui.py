"""A simple graphical interface for passgen.

Built with tkinter, which comes with the standard Python installer, so it
needs no extra packages. All the real work is done by generator.py.

Run it with:  python -m passgen.gui
"""

from __future__ import annotations

import sys
from typing import Tuple

try:
    import tkinter as tk
    from tkinter import ttk
except ImportError:  # tkinter isn't installed (some Linux setups)
    tk = None
    ttk = None

from . import __version__
from .generator import (
    PasswordError,
    describe_strength,
    estimate_entropy_bits,
    generate_password,
)

CLIPBOARD_CLEAR_SECONDS = 30
DEFAULT_LENGTH = 16
SLIDER_MIN = 8
SLIDER_MAX = 64
STRENGTH_BAR_MAX = 128  # bits of entropy that fill the strength bar completely

GUIDE_TEXT = (
    "1. A password is already made for you. Press \"Copy password\".\n"
    "2. Click the password box on the website and paste it with Ctrl+V.\n"
    "3. Save it in a password manager. This app doesn't remember anything.\n"
    "\n"
    "Tips: longer is stronger (16 or more is great), and every account should "
    "get its own password. If a website rejects the password, untick "
    "\"Symbols\" and make a new one.\n"
    "\n"
    f"The clipboard is cleared {CLIPBOARD_CLEAR_SECONDS} seconds after copying, "
    "or when you close this window."
)

OK_COLOR = "#2e7d32"
ERROR_COLOR = "#c62828"


def make_password(
    length: int,
    lowercase: bool,
    uppercase: bool,
    numbers: bool,
    symbols: bool,
    exclude_ambiguous: bool,
) -> Tuple[str, float, str]:
    """Generate a password and return (password, entropy_bits, strength_label).

    Raises PasswordError if the settings are invalid.
    """
    options = {
        "lowercase": lowercase,
        "uppercase": uppercase,
        "numbers": numbers,
        "symbols": symbols,
        "exclude_ambiguous": exclude_ambiguous,
    }
    password = generate_password(length, **options)
    bits = estimate_entropy_bits(length, **options)
    return password, bits, describe_strength(bits)


class PassgenApp:
    """The main window."""

    def __init__(self, root) -> None:
        self.root = root
        self._ready = False  # stops widgets firing callbacks while being built
        self._clear_job = None
        self._last_copied = None

        self.length = tk.IntVar(value=DEFAULT_LENGTH)
        self.lowercase = tk.BooleanVar(value=True)
        self.uppercase = tk.BooleanVar(value=True)
        self.numbers = tk.BooleanVar(value=True)
        self.symbols = tk.BooleanVar(value=True)
        self.exclude_ambiguous = tk.BooleanVar(value=False)
        self.password = tk.StringVar()
        self.strength_text = tk.StringVar()
        self.status = tk.StringVar()

        root.title("passgen - Password Generator")
        root.resizable(False, False)
        root.protocol("WM_DELETE_WINDOW", self.close)
        root.bind("<Return>", lambda _event: self.generate())

        self._build_widgets()
        self._ready = True
        self.generate()

    # ----- layout ---------------------------------------------------------

    def _build_widgets(self) -> None:
        frame = ttk.Frame(self.root, padding=16)
        frame.grid(row=0, column=0, sticky="nsew")

        ttk.Label(
            frame, text="Your new password", font=("Segoe UI", 12, "bold")
        ).grid(row=0, column=0, columnspan=2, sticky="w")

        # Read-only so it can't be edited by accident, but still selectable.
        self.entry = ttk.Entry(
            frame,
            textvariable=self.password,
            font=("Consolas", 16),
            width=30,
            state="readonly",
            justify="center",
        )
        self.entry.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(6, 8))

        self.strength_bar = ttk.Progressbar(
            frame, maximum=STRENGTH_BAR_MAX, mode="determinate"
        )
        self.strength_bar.grid(row=2, column=0, sticky="ew", padx=(0, 10))
        ttk.Label(frame, textvariable=self.strength_text, width=22).grid(
            row=2, column=1, sticky="w"
        )

        buttons = ttk.Frame(frame)
        buttons.grid(row=3, column=0, columnspan=2, sticky="ew", pady=12)
        buttons.columnconfigure(0, weight=1)
        buttons.columnconfigure(1, weight=1)
        ttk.Button(buttons, text="Copy password", command=self.copy).grid(
            row=0, column=0, sticky="ew", padx=(0, 6), ipady=6
        )
        ttk.Button(buttons, text="Make a new one", command=self.generate).grid(
            row=0, column=1, sticky="ew", ipady=6
        )

        self.status_label = ttk.Label(frame, textvariable=self.status)
        self.status_label.grid(row=4, column=0, columnspan=2, sticky="w")

        options = ttk.LabelFrame(frame, text="Options", padding=10)
        options.grid(row=5, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        options.columnconfigure(1, weight=1)

        ttk.Label(options, text="Length:").grid(row=0, column=0, sticky="w")
        tk.Scale(
            options,
            from_=SLIDER_MIN,
            to=SLIDER_MAX,
            orient="horizontal",
            variable=self.length,
            command=self._on_change,
            length=280,
        ).grid(row=0, column=1, sticky="ew", padx=(8, 0))

        choices = [
            ("Lowercase letters (a-z)", self.lowercase),
            ("Uppercase letters (A-Z)", self.uppercase),
            ("Numbers (0-9)", self.numbers),
            ("Symbols (!@#$...)", self.symbols),
            ("Avoid look-alike characters (l, 1, O, 0)", self.exclude_ambiguous),
        ]
        for row, (text, variable) in enumerate(choices, start=1):
            ttk.Checkbutton(
                options, text=text, variable=variable, command=self.generate
            ).grid(row=row, column=0, columnspan=2, sticky="w", pady=1)

        guide = ttk.LabelFrame(frame, text="Quick guide", padding=10)
        guide.grid(row=6, column=0, columnspan=2, sticky="ew", pady=(10, 0))
        ttk.Label(guide, text=GUIDE_TEXT, wraplength=440, justify="left").grid(
            row=0, column=0, sticky="w"
        )

        ttk.Label(
            frame,
            text=f"passgen v{__version__} - free and open source. "
            "Nothing is saved or sent anywhere.",
            foreground="gray",
        ).grid(row=7, column=0, columnspan=2, sticky="w", pady=(10, 0))

    # ----- actions --------------------------------------------------------

    def _on_change(self, _value=None) -> None:
        self.generate()

    def _set_status(self, text: str, error: bool = False) -> None:
        self.status.set(text)
        self.status_label.configure(foreground=ERROR_COLOR if error else OK_COLOR)

    def generate(self) -> None:
        """Make a new password using the current options."""
        if not self._ready:
            return
        try:
            password, bits, label = make_password(
                self.length.get(),
                self.lowercase.get(),
                self.uppercase.get(),
                self.numbers.get(),
                self.symbols.get(),
                self.exclude_ambiguous.get(),
            )
        except PasswordError as error:
            self.password.set("")
            self.strength_bar["value"] = 0
            self.strength_text.set("")
            self._set_status(str(error), error=True)
            return

        self.password.set(password)
        self.strength_bar["value"] = min(bits, STRENGTH_BAR_MAX)
        self.strength_text.set(f"Strength: {label.capitalize()}")
        self._set_status("New password ready. Press \"Copy password\".")

    def copy(self) -> None:
        """Copy the password and schedule the clipboard to be cleared."""
        password = self.password.get()
        if not password:
            return
        self.root.clipboard_clear()
        self.root.clipboard_append(password)
        self.root.update()  # hand the text over to the operating system now
        self._last_copied = password

        if self._clear_job is not None:
            self.root.after_cancel(self._clear_job)
        self._clear_job = self.root.after(
            CLIPBOARD_CLEAR_SECONDS * 1000, self._on_clear_timer
        )
        self._set_status(
            f"Copied! Paste it now. The clipboard clears in "
            f"{CLIPBOARD_CLEAR_SECONDS} seconds."
        )

    def _on_clear_timer(self) -> None:
        self._clear_job = None
        if self._clear_clipboard_if_ours():
            self._set_status("Clipboard cleared.")

    def _clear_clipboard_if_ours(self) -> bool:
        """Empty the clipboard, but only if it still holds our password.

        If you've copied something else in the meantime, that is left alone.
        """
        ours, self._last_copied = self._last_copied, None
        if not ours:
            return False
        try:
            current = self.root.clipboard_get()
        except tk.TclError:  # clipboard empty or holds something that isn't text
            return False
        if current != ours:
            return False
        self.root.clipboard_clear()
        self.root.update()
        return True

    def close(self) -> None:
        if self._clear_job is not None:
            self.root.after_cancel(self._clear_job)
            self._clear_job = None
        self._clear_clipboard_if_ours()
        self.root.destroy()


def _enable_sharp_text() -> None:
    """Stop Windows from blurring the window on high-resolution screens."""
    try:
        from ctypes import windll

        windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass  # not Windows, or not supported: no problem


def main() -> int:
    if tk is None:
        print(
            "The graphical version needs tkinter, which is missing from this "
            "Python install. On Linux, install it with: sudo apt install python3-tk",
            file=sys.stderr,
        )
        return 1

    _enable_sharp_text()
    try:
        root = tk.Tk()
    except tk.TclError as error:
        print(f"Could not open a window: {error}", file=sys.stderr)
        return 1

    PassgenApp(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
