"""Standalone entry point for PyInstaller.

cli.py uses a relative import (`from .app import ...`), which breaks when
PyInstaller/Python runs it directly as a top-level script ("attempted
relative import with no known parent package"). This wrapper imports the
installed breakbell package normally instead, so PyInstaller can freeze
it into a working executable.
"""
import sys

from breakbell.cli import _win_setup, main

_win_setup()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
