import argparse
import sys
import threading

from .app import BreakTimerApp
from .config import load_config, save_config
from .tray import TRAY_AVAILABLE, make_icon_image


def main():
    if sys.platform.startswith("win"):
        import ctypes
        try:
            console_hwnd = ctypes.windll.kernel32.GetConsoleWindow()
            if console_hwnd:
                ctypes.windll.user32.ShowWindow(console_hwnd, 0)
        except Exception:
            pass

    parser = argparse.ArgumentParser(description="Lightweight desktop break reminder timer")
    parser.add_argument("--no-tray", action="store_true",
                         help="Disable the system tray icon")
    args = parser.parse_args()

    config = load_config()
    app = BreakTimerApp(config=config)

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
        def toggle_pause():
            new_enabled = not app.config.get("enabled", True)
            new_config = dict(app.config)
            new_config["enabled"] = new_enabled
            save_config(new_config)
            app.root.after(0, lambda: app.apply_config(new_config))

        def start_tray():
            try:
                import pystray  # type: ignore
                menu = pystray.Menu(
                    pystray.MenuItem("Settings", lambda: app.root.after(0, open_settings), default=True),
                    pystray.MenuItem(
                        lambda item: "Pause breaks" if app.config.get("enabled", True) else "Resume breaks",
                        lambda: toggle_pause()
                    ),
                    pystray.MenuItem("Take a break now", lambda: app.root.after(0, app.trigger_break_now)),
                    pystray.MenuItem("Quit", lambda: quit_app()),
                )
                icon = pystray.Icon("breakbell", make_icon_image(), "BreakBell", menu)
                tray_icon_holder["icon"] = icon
                icon.run()
            except Exception:
                pass  # No usable tray backend on this system - app still runs fine without it

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
