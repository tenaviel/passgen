"""Command-line interface for passgen."""

from __future__ import annotations

import argparse
import sys
from typing import Dict, List, Optional

from . import __version__
from .clipboard import copy_to_clipboard
from .generator import (
    MAX_LENGTH,
    PasswordError,
    describe_strength,
    estimate_entropy_bits,
    generate_password,
)

DEFAULT_LENGTH = 16
MAX_COUNT = 100


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="passgen",
        description=(
            "Generate secure random passwords. Everything happens on your "
            "machine: nothing is stored, logged or sent anywhere."
        ),
        epilog=(
            "examples:\n"
            "  passgen                      16 characters, all character types\n"
            "  passgen -l 24 --no-symbols   24 letters and numbers\n"
            "  passgen -c                   generate and copy to the clipboard\n"
            "  passgen -i                   answer a few questions instead of flags"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "-l", "--length", type=int, default=DEFAULT_LENGTH,
        help=f"password length (default: {DEFAULT_LENGTH}, max: {MAX_LENGTH})",
    )
    parser.add_argument("--no-lowercase", action="store_true", help="leave out lowercase letters (a-z)")
    parser.add_argument("--no-uppercase", action="store_true", help="leave out uppercase letters (A-Z)")
    parser.add_argument("--no-numbers", action="store_true", help="leave out numbers (0-9)")
    parser.add_argument("--no-symbols", action="store_true", help="leave out symbols (!@#$...)")
    parser.add_argument(
        "-x", "--exclude-ambiguous", action="store_true",
        help="avoid look-alike characters (i, l, 1, L, o, 0, O)",
    )
    parser.add_argument(
        "-n", "--count", type=int, default=1,
        help=f"how many passwords to generate (default: 1, max: {MAX_COUNT})",
    )
    parser.add_argument("-c", "--copy", action="store_true", help="copy the password to the clipboard")
    parser.add_argument("-e", "--entropy", action="store_true", help="show an estimate of password strength")
    parser.add_argument("-i", "--interactive", action="store_true", help="ask for the settings step by step")
    parser.add_argument("-V", "--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _ask_yes_no(question: str, default: bool = True) -> bool:
    hint = "Y/n" if default else "y/N"
    while True:
        answer = input(f"{question} [{hint}]: ").strip().lower()
        if not answer:
            return default
        if answer in ("y", "yes"):
            return True
        if answer in ("n", "no"):
            return False
        print("Please answer y or n.")


def _ask_length(default: int) -> int:
    while True:
        answer = input(f"Password length [{default}]: ").strip()
        if not answer:
            return default
        if answer.isdigit():
            return int(answer)
        print("Please enter a whole number.")


def prompt_for_settings() -> Dict[str, object]:
    """Ask the user for settings interactively."""
    return {
        "length": _ask_length(DEFAULT_LENGTH),
        "lowercase": _ask_yes_no("Include lowercase letters?"),
        "uppercase": _ask_yes_no("Include uppercase letters?"),
        "numbers": _ask_yes_no("Include numbers?"),
        "symbols": _ask_yes_no("Include symbols?"),
        "exclude_ambiguous": _ask_yes_no("Avoid look-alike characters (l, 1, O, 0)?", default=False),
    }


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        if not 1 <= args.count <= MAX_COUNT:
            raise PasswordError(f"Count must be between 1 and {MAX_COUNT}.")
        if args.copy and args.count != 1:
            raise PasswordError("--copy only works with a single password.")

        if args.interactive:
            settings = prompt_for_settings()
        else:
            settings = {
                "length": args.length,
                "lowercase": not args.no_lowercase,
                "uppercase": not args.no_uppercase,
                "numbers": not args.no_numbers,
                "symbols": not args.no_symbols,
                "exclude_ambiguous": args.exclude_ambiguous,
            }

        passwords = [generate_password(**settings) for _ in range(args.count)]
    except PasswordError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    except (KeyboardInterrupt, EOFError):
        print("\nCancelled.", file=sys.stderr)
        return 130

    # Passwords go to stdout alone, so the output is clean to pipe or copy by hand.
    # Everything else goes to stderr.
    for password in passwords:
        print(password)

    if args.entropy:
        options = {k: v for k, v in settings.items() if k != "length"}
        bits = estimate_entropy_bits(settings["length"], **options)
        print(f"Estimated entropy: {bits:.1f} bits ({describe_strength(bits)})", file=sys.stderr)

    if args.copy:
        if copy_to_clipboard(passwords[0]):
            print("Copied to clipboard. Clear it when you're done with it.", file=sys.stderr)
        else:
            print(
                "Could not copy automatically (no clipboard tool found). "
                "Select and copy the password above instead.",
                file=sys.stderr,
            )
            return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
