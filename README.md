# BreakBell

A tiny, lightweight desktop break reminder. Runs quietly in the system tray
and shows a clean on-screen break card at whatever interval you set —
countdown, progress bar, break sound, and a one-click "Cancel Break" if you
need to skip it. Fully configurable through a Settings window, no editing
config files by hand.

## Install (Windows)

**Recommended: the installer.** Download `BreakBell-Setup.exe` from the
[Releases page](../../releases). It installs BreakBell properly:

- Installs to Program Files
- Adds a Start Menu shortcut
- Optional desktop shortcut
- Optional "launch automatically when Windows starts"
- Adds a real uninstaller (Settings → Apps, or Start Menu)

> **Windows SmartScreen/Defender note:** this is a small, unsigned
> open-source tool, so Windows may show a warning the first time you run the
> installer since it doesn't yet have an established reputation. Click
> **More info → Run anyway** if that happens. The source code is fully open
> here for you to verify nothing's actually wrong.

**Alternative: portable zip.** If you'd rather not install anything, grab
`breakbell-windows.zip` instead, extract it, and run `breakbell.exe` inside
the extracted folder. Keep the whole folder together — the executable needs
the files next to it. With this option you'll need to set up auto-start
yourself (see below) since there's no installer to offer it.

## Install (macOS / Linux)

Grab `breakbell-macos.zip` or `breakbell-linux.zip` from the
[Releases page](../../releases), extract, and run the `breakbell` file
inside. macOS may ask you to allow it in **System Settings → Privacy &
Security** the first time (Gatekeeper, since it's unsigned).

### Alternative: install with pip (any OS, if you have Python)

```bash
pip install git+https://github.com/saadisafdar/breakbell.git
breakbell
```

## Usage

Just run it — it lives in your system tray (bottom-right on Windows, near
the clock). Right-click the tray icon for:

- **Settings** — configure everything: break frequency, break length, title,
  message, and break sound (with a preview button), all applied instantly,
  no restart needed
- **Take a break now** — trigger a break immediately
- **Quit** — exit the app

If there's no system tray available (or you pass `--no-tray`), the Settings
window opens automatically on launch instead.

```bash
breakbell            # normal run, with tray icon
breakbell --no-tray  # run without a tray icon
```

Settings are saved to a per-user config file and persist across restarts.

## Run it automatically at login (optional)

If you used the Windows installer, just tick **"Launch BreakBell
automatically when Windows starts"** during setup — nothing else needed. If
you skipped that or you're on the portable zip / another OS:

**Windows:** Press `Win+R` → `shell:startup` → Enter. Add a shortcut to
`breakbell.exe` inside your extracted folder (or, if installed via pip,
to `breakbell.exe` in your Python Scripts folder).

**macOS:** System Settings → General → Login Items → add the app.

**Linux:** Add a `.desktop` file to `~/.config/autostart/`:
```ini
[Desktop Entry]
Type=Application
Exec=/path/to/breakbell
Name=BreakBell
```

## Development

```bash
git clone https://github.com/saadisafdar/breakbell.git
cd breakbell
pip install -e .
breakbell
```

Requires Python 3.8+ with tkinter (bundled by default on Windows/macOS
installers; on Linux, `sudo apt install python3-tk` if it's missing).

Building the Windows installer locally requires [Inno Setup](https://jrsoftware.org/isinfo.php):
```
pyinstaller --onedir --windowed --noupx --name breakbell --hidden-import=PIL._tkinter_finder --add-data "src/breakbell/assets/sounds;breakbell/assets/sounds" --add-data "src/breakbell/assets/icon.png;breakbell/assets" run_breakbell.py
iscc installer.iss
```

## License

MIT — see [LICENSE](LICENSE).
