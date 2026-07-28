"""Settings window for BreakBell - dark-themed, matches the app's style."""
import tkinter as tk
from tkinter import ttk

from . import audio
from . import tray

BG = "#1D1D1D"
PANEL = "#1a1a1d"
FIELD = "#232326"
TEXT = "#f2f2f3"
SUBTEXT = "#9a9aa0"
ACCENT = "#103046"


def _hms_row(parent, label_text, total_seconds):
    """Builds an 'HH h : MM m : SS s' row of spinboxes. Returns a getter function."""
    tk.Label(parent, text=label_text, font=("Segoe UI", 10, "bold"),
              bg=BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 6))

    row = tk.Frame(parent, bg=FIELD)
    row.pack(anchor="w", pady=(0, 16))

    h, rem = divmod(int(total_seconds), 3600)
    m, s = divmod(rem, 60)

    def spin(initial, maximum, suffix):
        var = tk.StringVar(value=f"{initial:02d}")
        sb = tk.Spinbox(row, from_=0, to=maximum, width=3, textvariable=var,
                          font=("Segoe UI", 11), bg=FIELD, fg=TEXT,
                          buttonbackground=FIELD, relief="flat", justify="center",
                          insertbackground=TEXT)
        sb.pack(side="left", padx=(8, 2), pady=8)
        tk.Label(row, text=suffix, font=("Segoe UI", 10), bg=FIELD, fg=SUBTEXT).pack(side="left")
        return var

    h_var = spin(h, 23, "h")
    tk.Label(row, text=":", bg=FIELD, fg=SUBTEXT).pack(side="left")
    m_var = spin(m, 59, "m")
    tk.Label(row, text=":", bg=FIELD, fg=SUBTEXT).pack(side="left")
    s_var = spin(s, 59, "s")

    def get_seconds():
        try:
            return int(h_var.get()) * 3600 + int(m_var.get()) * 60 + int(s_var.get())
        except ValueError:
            return total_seconds

    return get_seconds


class SettingsWindow:
    def __init__(self, root, config, on_save):
        self.on_save = on_save
        self.win = tk.Toplevel(root)
        self.win.title("BreakBell Settings")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        try:
            self._icon_img = tk.PhotoImage(file=tray.icon_path())
            self.win.iconphoto(True, self._icon_img)
        except Exception:
            pass

        canvas = tk.Canvas(self.win, bg=BG, highlightthickness=0)
        vscroll = tk.Scrollbar(self.win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        pad = tk.Frame(canvas, bg=BG, padx=24, pady=20)
        pad_window = canvas.create_window((0, 0), window=pad, anchor="nw")

        def _sync_scrollregion(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _sync_width(event):
            canvas.itemconfigure(pad_window, width=event.width)

        pad.bind("<Configure>", _sync_scrollregion)
        canvas.bind("<Configure>", _sync_width)

        def _on_mousewheel(event):
            if hasattr(event, "num") and event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif hasattr(event, "num") and event.num == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

        # Breaks header
        header = tk.Frame(pad, bg=BG)
        header.pack(fill="x", pady=(0, 18))
        tk.Label(header, text="Breaks", font=("Segoe UI", 15, "bold"),
                  bg=BG, fg=TEXT).pack(side="left")

        self.enabled_var = tk.BooleanVar(value=config.get("enabled", True))
        cb = tk.Checkbutton(
            header, text="Enable break reminders", variable=self.enabled_var,
            font=("Segoe UI", 10), bg=BG, fg=TEXT, selectcolor=FIELD,
            activebackground=BG, activeforeground=TEXT, cursor="hand2"
        )
        cb.pack(side="right")

        # Frequency / Length, side by side
        freq_length_row = tk.Frame(pad, bg=BG)
        freq_length_row.pack(fill="x")
        freq_col = tk.Frame(freq_length_row, bg=BG)
        freq_col.pack(side="left", padx=(0, 28))
        length_col = tk.Frame(freq_length_row, bg=BG)
        length_col.pack(side="left")
        self.get_work_seconds = _hms_row(freq_col, "Frequency", config.get("work_seconds", 1200))
        self.get_break_seconds = _hms_row(length_col, "Length", config.get("break_seconds", 60))

        # Audio (moved above Title/Message)
        tk.Label(pad, text="Break sound", font=("Segoe UI", 10, "bold"),
                  bg=BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 6))
        self.sound_var = tk.StringVar(value=config.get("sound", "Ping"))
        sound_box = ttk.Combobox(pad, textvariable=self.sound_var, state="readonly",
                                   values=audio.available_sounds(), width=20)
        sound_box.pack(anchor="w", pady=(0, 8))
        tk.Button(pad, text="Preview sound", command=self._preview_sound,
                   bg=FIELD, fg=TEXT, relief="flat", padx=10, pady=4,
                   activebackground=FIELD, activeforeground=TEXT, cursor="hand2"
                   ).pack(anchor="w", pady=(0, 20))

        # Title
        tk.Label(pad, text="Title", font=("Segoe UI", 10, "bold"),
                  bg=BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 6))
        self.title_var = tk.StringVar(value=config.get("title", "Take a break"))
        tk.Entry(pad, textvariable=self.title_var, font=("Segoe UI", 11),
                  bg=FIELD, fg=TEXT, relief="flat", insertbackground=TEXT
                  ).pack(fill="x", ipady=6, pady=(0, 16))

        # Message
        tk.Label(pad, text="Message", font=("Segoe UI", 10, "bold"),
                  bg=BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 6))
        self.message_text = tk.Text(pad, height=4, font=("Segoe UI", 11), bg=FIELD, fg=TEXT,
                                      relief="flat", insertbackground=TEXT, wrap="word")
        self.message_text.insert("1.0", config.get("message", ""))
        self.message_text.pack(fill="x", pady=(0, 20))

        # Save / Cancel
        btn_row = tk.Frame(pad, bg=BG)
        btn_row.pack(fill="x", pady=(4, 0))
        tk.Button(btn_row, text="Cancel", command=self._on_close,
                   bg=PANEL, fg=TEXT, relief="flat", padx=16, pady=8,
                   activebackground=PANEL, activeforeground=TEXT, cursor="hand2"
                   ).pack(side="right", padx=(8, 0))
        tk.Button(btn_row, text="Save", command=self._save,
                   bg=ACCENT, fg="white", relief="flat", padx=16, pady=8,
                   font=("Segoe UI", 10, "bold"), activebackground="#1c4a68",
                   activeforeground="white", cursor="hand2"
                   ).pack(side="right")

        self._style_combobox()

        self.win.update_idletasks()
        content_width = pad.winfo_reqwidth()
        content_height = pad.winfo_reqheight()
        screen_w = self.win.winfo_screenwidth()
        screen_h = self.win.winfo_screenheight()

        width = content_width + vscroll.winfo_reqwidth()
        height = min(content_height, screen_h - 100)
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.win.update_idletasks()
        self.win.minsize(min(width, 380), 300)

        self.win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _on_close(self):
        try:
            self.win.unbind_all("<MouseWheel>")
            self.win.unbind_all("<Button-4>")
            self.win.unbind_all("<Button-5>")
        except tk.TclError:
            pass
        self.win.destroy()

    def _style_combobox(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TCombobox", fieldbackground=FIELD, background=FIELD,
                          foreground=TEXT, arrowcolor=TEXT)

    def _preview_sound(self):
        audio.play_sound(self.sound_var.get())

    def _save(self):
        new_config = {
            "enabled": bool(self.enabled_var.get()),
            "work_seconds": max(1, self.get_work_seconds()),
            "break_seconds": max(1, self.get_break_seconds()),
            "title": self.title_var.get().strip() or "Take a break",
            "message": self.message_text.get("1.0", "end").strip(),
            "sound": self.sound_var.get(),
        }
        self._on_close()
        self.on_save(new_config)