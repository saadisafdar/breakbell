import argparse
import sys
import threading

from .app import BreakTimerApp
from .config import load_config, save_config
from .tray import TRAY_AVAILABLE, make_icon_image
from . import updater


def _win_setup():
    """Suppress the console window and set the AppUserModelID on Windows."""
    if not sys.platform.startswith("win"):
        return
    import ctypes
    try:
        myappid = "saadisafdar.breakbell.app.1"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass
    try:
        console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if console_hwnd:
            ctypes.windll.user32.ShowWindow(console_hwnd, 0)
    except Exception:
        pass


def main():
    _win_setup()

    parser = argparse.ArgumentParser(description="Lightweight desktop break reminder timer")
    parser.add_argument("--no-tray", action="store_true",
                         help="Disable the system tray icon")
    args = parser.parse_args()

    config = load_config()
    app = BreakTimerApp(config=config)

    # Check for updates asynchronously at launch
    updater.check_for_updates_async()

    tray_icon_holder = {}

    def open_settings():
        # Import here - Toplevel must be created on the main thread via .after()
        from .settings_window import SettingsWindow

        def on_save(new_config):
            save_config(new_config)
            app.apply_config(new_config)

        SettingsWindow(app.root, app.config, on_save=on_save)

    def quit_app():
        if tray_icon_holder.get("icon"):
            tray_icon_holder["icon"].stop()
        app.root.after(0, app.root.destroy)

    if TRAY_AVAILABLE and not args.no_tray:
        def start_tray():
            try:
                import pystray  # type: ignore

                def _settings(*_):
                    app.root.after(0, open_settings)

                def _break_now(*_):
                    app.root.after(0, app.trigger_break_now)

                def _quit(*_):
                    app.root.after(0, quit_app)

                menu = pystray.Menu(
                    pystray.MenuItem("Settings", _settings, default=True),
                    pystray.MenuItem("Take a break now", _break_now),
                    pystray.Menu.SEPARATOR,
                    pystray.MenuItem("Quit", _quit),
                )
                icon = pystray.Icon("breakbell", make_icon_image(), "BreakBell", menu=menu)
                tray_icon_holder["icon"] = icon
                icon.run()
            except Exception:
                pass  # No usable tray backend - app still runs without it

        threading.Thread(target=start_tray, daemon=True).start()

    else:
        # No tray available - open Settings immediately so the app is still reachable
        app.root.after(500, open_settings)

    app.run()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(0)
