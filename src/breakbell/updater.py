"""Lightweight, non-blocking update checker for BreakBell using stdlib urllib."""
import json
import re
import threading
import urllib.request
import webbrowser

from . import __version__

GITHUB_RELEASES_URL = "https://api.github.com/repos/saadisafdar/breakbell/releases/latest"

_latest_release_info = None


def _is_newer_version(latest_str, current_str):
    try:
        latest = [int(x) for x in re.findall(r"\d+", latest_str)]
        current = [int(x) for x in re.findall(r"\d+", current_str)]
        while len(latest) < 3:
            latest.append(0)
        while len(current) < 3:
            current.append(0)
        return latest > current
    except Exception:
        return False


def check_for_updates_async(on_complete=None):
    def _fetch():
        global _latest_release_info
        try:
            req = urllib.request.Request(
                GITHUB_RELEASES_URL,
                headers={"User-Agent": "BreakBell-App"}
            )
            with urllib.request.urlopen(req, timeout=5) as resp:
                if resp.status == 200:
                    data = json.loads(resp.read().decode("utf-8"))
                    tag = data.get("tag_name", "").lstrip("v")
                    html_url = data.get(
                        "html_url",
                        "https://github.com/saadisafdar/breakbell/releases/latest"
                    )
                    if tag and _is_newer_version(tag, __version__):
                        _latest_release_info = {
                            "version": tag,
                            "url": html_url
                        }
                        if on_complete:
                            on_complete(_latest_release_info)
        except Exception:
            pass  # Offline or rate-limited - fail silently without affecting app

    threading.Thread(target=_fetch, daemon=True).start()


def get_update_info():
    return _latest_release_info


def open_release_page():
    url = (
        _latest_release_info["url"]
        if _latest_release_info
        else "https://github.com/saadisafdar/breakbell/releases/latest"
    )
    webbrowser.open(url)
