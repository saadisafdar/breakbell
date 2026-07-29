"""Lightweight, non-blocking update checker for BreakBell.

Only shows a notification when the remote version is *strictly newer*
than the running version (e.g. remote=1.2.0, local=1.1.0 → show;
remote=1.1.0, local=1.1.0 → hide).
"""
import json
import re
import threading
import urllib.request
import webbrowser

from . import __version__

GITHUB_RELEASES_URL = (
    "https://api.github.com/repos/saadisafdar/breakbell/releases/latest"
)

# Populated by the background thread; None means "no newer release found".
_latest_release_info = None


def _parse_version(version_str: str) -> tuple:
    """Return a comparable tuple of ints, e.g. '1.2.0' → (1, 2, 0)."""
    parts = [int(x) for x in re.findall(r"\d+", version_str)]
    # Pad to at least 3 components so comparisons are always well-defined.
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts)


def _is_newer(remote: str, local: str) -> bool:
    """Return True only when remote is strictly greater than local."""
    try:
        return _parse_version(remote) > _parse_version(local)
    except Exception:
        return False


def check_for_updates_async(on_complete=None):
    """Fetch the latest GitHub release in a daemon thread; never blocks the UI."""

    def _fetch():
        global _latest_release_info
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_URL,
                headers={"User-Agent": "BreakBell-App"},
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status != 200:
                    return
                # Read only what we need — avoids holding large payloads in RAM.
                raw = resp.read(8192).decode("utf-8", errors="replace")

            data = json.loads(raw)
            tag = data.get("tag_name", "").lstrip("v").strip()
            html_url = data.get(
                "html_url",
                "https://github.com/saadisafdar/breakbell/releases/latest",
            )

            if tag and _is_newer(tag, __version__):
                _latest_release_info = {"version": tag, "url": html_url}
                if on_complete:
                    on_complete(_latest_release_info)
            # If remote ≤ local: leave _latest_release_info as None → no banner.

        except Exception:
            pass  # Offline / rate-limited / malformed JSON — fail silently.

    threading.Thread(target=_fetch, daemon=True).start()


def get_update_info():
    """Return update dict if a newer version exists, else None."""
    return _latest_release_info


def open_release_page():
    url = (
        _latest_release_info["url"]
        if _latest_release_info
        else "https://github.com/saadisafdar/breakbell/releases/latest"
    )
    webbrowser.open(url)
