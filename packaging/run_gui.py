"""Entry point used by PyInstaller to build the Windows app."""

from passgen.gui import main

if __name__ == "__main__":
    raise SystemExit(main())
