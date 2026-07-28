"""Standalone entry point for PyInstaller.

cli.py uses a relative import (`from .app import ...`), which breaks when
PyInstaller/Python runs it directly as a top-level script ("attempted
relative import with no known parent package"). This wrapper imports the
installed breakbell package normally instead, so PyInstaller can freeze
it into a working executable.
"""
import sys

if sys.platform.startswith("win"):
    import ctypes
    try:
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd:
            ctypes.windll.user32.ShowWindow(console_hwnd, 0)
    except Exception:
        pass

from breakbell.cli import main

if __name__ == "__main__":
    main()
