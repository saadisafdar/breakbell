"""Optional system tray icon support for BreakBell.

Uses pystray + Pillow if available. If either is missing (e.g. a minimal
Linux box with no tray daemon), tray support is silently skipped and the
app still runs exactly as before - just without a tray icon.
"""

import os

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import pystray  # noqa: F401
    TRAY_AVAILABLE = PIL_AVAILABLE
except Exception:
    # Covers ImportError as well as backend-selection errors pystray can
    # raise on systems missing a tray backend (e.g. no GTK/AppIndicator).
    TRAY_AVAILABLE = False

_ASSET_DIR = os.path.join(os.path.dirname(__file__), "assets")
_ICON_SM_PATH = os.path.join(_ASSET_DIR, "icon_sm.png")
_ICON_PATH = _ICON_SM_PATH if os.path.exists(_ICON_SM_PATH) else os.path.join(_ASSET_DIR, "icon.png")
_cached_icon = None


def make_icon_image(size=(64, 64)):
    global _cached_icon
    if _cached_icon is None:
        if PIL_AVAILABLE:
            im = Image.open(_ICON_PATH).convert("RGBA")
            im.thumbnail(size, Image.Resampling.LANCZOS)
            _cached_icon = im
    return _cached_icon


def icon_path():
    """Path to the lightweight bundled icon PNG, for use as a Tk window icon."""
    return _ICON_PATH
