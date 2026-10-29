# passgen

[![Tests](https://github.com/tenaviel/passgen/actions/workflows/tests.yml/badge.svg)](https://github.com/tenaviel/passgen/actions/workflows/tests.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License: MIT](https://img.shields.io/badge/license-MIT-green)
![Dependencies: none](https://img.shields.io/badge/dependencies-none-brightgreen)

A small, secure, **local** password generator for the command line.
No accounts, no network, no dependencies, no storage. Just random passwords, generated on your own machine using Python's [`secrets`](https://docs.python.org/3/library/secrets.html) module.

## Features

- Choose the length and which character types to include (lowercase, uppercase, numbers, symbols)
- Guarantees at least one character from every selected type
- Optional "avoid look-alike characters" mode (`i l 1 L o 0 O`)
- A simple window with a slider, tick boxes and a built-in guide, plus a ready-to-run Windows app
- Copy to clipboard with one click (the app clears it again after 30 seconds)
- Clean output: the password is the only thing printed to stdout, so it pipes nicely
- Interactive mode for people who don't like flags
- Strength estimate (entropy) if you want one
- Pure standard library, easy to read and audit (the core logic is under 100 lines)

## Requirements

Python 3.10 or newer (not needed if you use the Windows app below). That's it.

## Easiest way: the app (no commands needed)

1. Open the [latest release](https://github.com/tenaviel/passgen/releases/latest) and download **passgen.exe**.
2. Double-click it. A window opens with a password already made for you.
3. Click **Copy password**, then paste it (Ctrl+V) wherever you need it.

Use the slider and tick boxes to change the length or leave out character types. The strength bar updates as you go, and a short guide is built into the window.

**About the Windows warning:** the first time you run it, Windows may show a blue *"Windows protected your PC"* screen. That happens to every program that isn't code-signed (signing certificates cost money), not because something is wrong. Click **More info**, then **Run anyway**. If you'd rather not trust a downloaded file, you can check it yourself:

- The exe is built automatically by GitHub from this repository's code (see [`.github/workflows/build-exe.yml`](.github/workflows/build-exe.yml)), and each release includes a `passgen.exe.sha256` file. In PowerShell, `Get-FileHash passgen.exe` should print the same hash.
- Or skip the exe and run the window from source: `python -m passgen.gui` (see below).

## Command-line quick start

```bash
git clone https://github.com/tenaviel/passgen.git
cd passgen
python -m passgen
```

Example output (yours will differ, obviously):

```
SK;s63{U:}F4/h^.
```

On Windows, use `py -m passgen` if `python` isn't found.

### Window from source

```bash
python -m passgen.gui
```

Needs tkinter, which is included with the standard Python installer for Windows and macOS. On Linux, install it with `sudo apt install python3-tk`.

### Optional: install it as a `passgen` command

```bash
pip install .
passgen
```

Or, to keep it out of your other Python packages, use [pipx](https://pipx.pypa.io/):

```bash
pipx install git+https://github.com/tenaviel/passgen.git
```

## Usage

```
passgen [options]
```

| Option | Description | Default |
| --- | --- | --- |
| `-l`, `--length N` | Password length (1 to 1024) | `16` |
| `--no-lowercase` | Leave out lowercase letters (`a-z`) | included |
| `--no-uppercase` | Leave out uppercase letters (`A-Z`) | included |
| `--no-numbers` | Leave out numbers (`0-9`) | included |
| `--no-symbols` | Leave out symbols (`!@#$%^&*()-_=+[]{};:,.?/~`) | included |
| `-x`, `--exclude-ambiguous` | Avoid look-alike characters (`i l 1 L o 0 O`) | off |
| `-n`, `--count N` | Generate N passwords (1 to 100) | `1` |
| `-c`, `--copy` | Copy the password to the clipboard | off |
| `-e`, `--entropy` | Show an estimated strength (printed to stderr) | off |
| `-i`, `--interactive` | Answer prompts instead of using flags | off |
| `-V`, `--version` | Show the version | |
| `-h`, `--help` | Show help | |

### Examples

```bash
# Default: 16 characters, all character types
passgen

# 24 characters, letters and numbers only (handy for sites that reject symbols)
passgen -l 24 --no-symbols

# A password that's easy to read aloud or type from paper
passgen -l 12 -x

# Generate and copy to the clipboard in one go
passgen -c

# Five options to pick from
passgen -n 5

# See how strong the result is
passgen -l 20 -e

# Walk through the settings step by step
passgen -i
```

### Clipboard support

`--copy` uses the clipboard tool your system already has, so there's nothing extra to install on most machines:

| OS | Tool used |
| --- | --- |
| macOS | `pbcopy` (built in) |
| Windows | `clip` (built in) |
| Linux (Wayland) | `wl-copy` (package `wl-clipboard`) |
| Linux (X11) | `xclip` or `xsel` |
| WSL | `clip.exe` |

If no tool is found, passgen tells you and you can copy the password from the terminal by hand.

## How it works

1. It builds a pool of characters for each selected type.
2. It picks **one** character from each pool, so every selected type is guaranteed to appear.
3. It fills the remaining length with characters picked from the combined pool.
4. It shuffles everything so the guaranteed characters don't sit in predictable positions.

Every random choice uses `secrets.choice()` and `secrets.SystemRandom().shuffle()`, which draw from your operating system's cryptographically secure random number generator. Python's regular `random` module is deliberately never used: it is designed for simulations and games, not secrets, and its output can be predicted if an attacker learns enough about its internal state.

## Security notes

Please read these. A password generator is only as safe as the way you handle what it produces.

- **Everything is local.** passgen makes no network requests and writes nothing to disk. There is no history, no log, no telemetry.
- **The password is shown in your terminal.** It may stay in your scrollback, and anyone looking at your screen can see it. Clear the terminal if that matters.
- **The Windows app is not code-signed**, so Windows will warn you the first time you run it. See the section above for how to verify it.
- **The clipboard is not private.** Other programs can read it, and clipboard managers or cloud clipboard sync (Windows clipboard history, Universal Clipboard, etc.) may store it. The app clears the clipboard 30 seconds after copying (or when you close it), but that can't reach Windows clipboard history (Win+V), which may keep a copy. The command-line `--copy` does **not** clear anything, so paste it where you need it, then copy something harmless over it.
- **It can't protect a compromised computer.** Malware, keyloggers and malicious browser extensions can capture passwords no matter how they were generated.
- **It is not a password manager.** passgen doesn't remember anything. Use a reputable password manager to store what you generate, and use a unique password for every account.
- **The entropy figure is an estimate.** It assumes an attacker knows your settings and nothing else, and it ignores the tiny effect of the "at least one of each type" rule. It's a ballpark, not a guarantee.
- **Length matters more than complexity.** For important accounts, prefer 16+ characters. A longer password beats a shorter one with more symbols.
- **Some sites have odd rules.** If a site rejects a password, try `--no-symbols` or a different length. Quotes, backslashes and spaces are never generated, to avoid shell and form problems.
- **No independent audit.** The code is small and written to be read, so please read it. Found a security issue? Open a GitHub issue, or report it privately through the repository's *Security* tab if you'd rather not disclose it publicly.

## Project layout

```
passgen/
├── passgen/
│   ├── __init__.py      # version number
│   ├── __main__.py      # enables `python -m passgen`
│   ├── cli.py           # argument parsing and output
│   ├── clipboard.py     # cross-platform clipboard helper
│   ├── gui.py           # the window (tkinter)
│   └── generator.py     # the actual password logic
├── packaging/           # entry point used to build the Windows app
├── tests/               # unit tests (standard library only)
├── .github/workflows/   # automated tests + Windows app build
├── pyproject.toml
├── LICENSE
└── README.md
```

## Development

No dependencies are needed to run the tests:

```bash
python -m unittest -v
```

The project also works with `pytest` if you prefer it (`pip install pytest && pytest`).

Contributions are welcome. Keep the project simple, dependency-free and readable, add tests for new behavior, and make sure the test suite passes before opening a pull request.

## License

[MIT](LICENSE)
