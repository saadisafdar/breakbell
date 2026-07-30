"""Settings window for BreakBell - clean reference design with 100% custom curved controls."""
import tkinter as tk

from . import audio
from . import tray
from .utils import _draw_rounded_polygon

# ── Colour palette ──────────────────────────────────────────────────────────
BG          = "#dbebf0"   # outer ice-teal background
CARD_BG     = "#ffffff"   # card background
CARD_BORDER = "#bce1ea"   # card border / separator
FIELD_BG    = "#e4f2f6"   # input field background (ice teal fill)
FIELD_BD    = "#b8dfe9"   # input border
TEXT        = "#1a1a1a"   # primary text
SUBTEXT     = "#527782"   # muted / label text
ACCENT      = "#1F9FBC"   # save button / active accent
ACCENT_HV   = "#17839b"   # save button hover
FONT        = "Segoe UI"


class _TimeEntry(tk.Frame):
    """Segmented  HH h : MM m : SS s  entry.

    - Only digit keys accepted; h / m / s / ':' are read-only labels.
    - Click or Tab into a segment selects its text immediately.
    - Typing 2 digits auto-advances to the next segment.
    - Leaving a segment (FocusOut) zero-pads a single digit  (5 → 05).
    - Right / Left arrows jump between segments at field boundaries.
    - Tab / Shift-Tab cycle through segments without leaving the widget.
    """

    def __init__(self, parent, seconds=0, **kw):
        super().__init__(parent, bg=FIELD_BG, **kw)

        vcmd = (self.register(self._only_digits), "%P")
        entry_kw = dict(
            font=(FONT, 10), bg=FIELD_BG, fg=TEXT,
            relief="flat", bd=0, highlightthickness=0,
            justify="center", width=2,
            validate="key", validatecommand=vcmd,
            insertbackground=TEXT,
        )
        lbl_kw = dict(bg=FIELD_BG, fg=TEXT, font=(FONT, 10))

        self._vars    = [tk.StringVar(), tk.StringVar(), tk.StringVar()]
        self._hv, self._mv, self._sv = self._vars

        self._entries = [tk.Entry(self, textvariable=v, **entry_kw) for v in self._vars]
        self._he, self._me, self._se = self._entries

        self._he.pack(side="left")
        tk.Label(self, text=" h : ", **lbl_kw).pack(side="left")
        self._me.pack(side="left")
        tk.Label(self, text=" m : ", **lbl_kw).pack(side="left")
        self._se.pack(side="left")
        tk.Label(self, text=" s",   **lbl_kw).pack(side="left")

        for i, entry in enumerate(self._entries):
            entry.bind("<FocusIn>",   self._on_focus)
            entry.bind("<Button-1>",  self._on_focus)
            entry.bind("<FocusOut>",  lambda e, i=i: self._pad(self._vars[i]))
            # Only advance on digit keys — ignore Tab/Backspace/arrows
            entry.bind("<KeyRelease>", lambda e, i=i: self._on_key(e, i))
            # Explicit navigation
            entry.bind("<Right>",     lambda e, i=i: self._on_right(e, i))
            entry.bind("<Left>",      lambda e, i=i: self._on_left(e, i))
            entry.bind("<Tab>",       lambda e, i=i: self._step(i, +1))
            entry.bind("<Shift-Tab>", lambda e, i=i: self._step(i, -1))

        self.set_seconds(seconds)

    # ── internal helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _only_digits(value: str) -> bool:
        """Validation: allow only 0-2 digit characters."""
        return value == "" or (value.isdigit() and len(value) <= 2)

    @staticmethod
    def _on_focus(event):
        """Select the full content of a segment when it gains focus."""
        w = event.widget
        w.after_idle(lambda: w.select_range(0, "end"))

    def _pad(self, var: tk.StringVar):
        """Zero-pad on blur: '' → '00', '5' → '05', '12' left alone."""
        val = var.get()
        if len(val) == 2:           # already correct, skip set() to avoid re-triggering
            return
        var.set("00" if not val.isdigit() else f"{int(val):02d}")

    def _on_key(self, event, idx: int):
        """After a digit key is released, auto-advance if 2 digits are filled."""
        # Ignore non-digit keys (Tab, Backspace, arrows, etc.)
        if not (event.char and event.char.isdigit()):
            return
        if len(self._vars[idx].get()) >= 2 and idx < len(self._entries) - 1:
            self._entries[idx + 1].focus_set()

    def _on_right(self, event, idx: int):
        """Jump forward when cursor is at the rightmost position."""
        e = event.widget
        if e.index(tk.INSERT) >= len(e.get()) and idx < len(self._entries) - 1:
            self._pad(self._vars[idx])
            self._entries[idx + 1].focus_set()
            return "break"          # suppress default cursor movement

    def _on_left(self, event, idx: int):
        """Jump backward when cursor is at position 0."""
        e = event.widget
        if e.index(tk.INSERT) == 0 and idx > 0:
            self._pad(self._vars[idx])
            prev = self._entries[idx - 1]
            prev.focus_set()
            prev.icursor(tk.END)    # land at the end of the previous segment
            return "break"

    def _step(self, idx: int, direction: int):
        """Tab/Shift-Tab: move to adjacent segment and stay inside the widget."""
        self._pad(self._vars[idx])
        target = idx + direction
        if 0 <= target < len(self._entries):
            self._entries[target].focus_set()
        return "break"              # always suppress default Tab traversal

    # ── public API ───────────────────────────────────────────────────────────

    def set_seconds(self, total: int):
        total = max(0, int(total))
        h, rem = divmod(total, 3600)
        m, s   = divmod(rem, 60)
        self._hv.set(f"{h:02d}")
        self._mv.set(f"{m:02d}")
        self._sv.set(f"{s:02d}")

    def get_seconds(self) -> int:
        for v in self._vars:
            self._pad(v)            # ensure all segments are padded before reading
        try:
            return (int(self._hv.get()) * 3600
                    + int(self._mv.get()) * 60
                    + int(self._sv.get()))
        except ValueError:
            return 0


class SettingsWindow:
    def __init__(self, root, config, on_save):
        self.on_save   = on_save
        self._config   = config

        win = tk.Toplevel(root)
        self.win = win
        win.title("Settings")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.attributes("-topmost", True)

        try:
            self._icon_img = tk.PhotoImage(file=tray.icon_path())
            win.iconphoto(True, self._icon_img)
        except Exception:
            pass

        W, H = 540, 440
        canvas = tk.Canvas(win, bg=BG, width=W, height=H, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # 1. Main White Card Panel (rounded r=16)
        _draw_rounded_polygon(canvas, 16, 16, W-16, H-16, r=16, fill=CARD_BG, outline=CARD_BORDER, width=1)

        # Header Breaks
        canvas.create_text(40, 48, text="Breaks", font=(FONT, 14, "bold"), fill=TEXT, anchor="w")

        # Save & Cancel Buttons (both equal width = 60px, height = 30px)
        save_bg = _draw_rounded_polygon(canvas, W-165, 32, W-105, 62, r=6, fill=ACCENT, outline="")
        save_txt = canvas.create_text(W-135, 47, text="Save", font=(FONT, 10, "bold"), fill="white")

        cancel_bg = _draw_rounded_polygon(canvas, W-98, 32, W-38, 62, r=6, fill=CARD_BG, outline=FIELD_BD, width=1)
        cancel_txt = canvas.create_text(W-68, 47, text="Cancel", font=(FONT, 10), fill=TEXT)

        for item in (save_bg, save_txt):
            canvas.tag_bind(item, "<Button-1>", lambda _e: self._save())
            canvas.tag_bind(item, "<Enter>", lambda _e: canvas.config(cursor="hand2"))
            canvas.tag_bind(item, "<Leave>", lambda _e: canvas.config(cursor=""))

        for item in (cancel_bg, cancel_txt):
            canvas.tag_bind(item, "<Button-1>", lambda _e: self._on_close())
            canvas.tag_bind(item, "<Enter>", lambda _e: canvas.config(cursor="hand2"))
            canvas.tag_bind(item, "<Leave>", lambda _e: canvas.config(cursor=""))

        # Separator line
        canvas.create_line(40, 76, W-40, 76, fill="#cbe3ea", width=1)

        # Field Labels
        canvas.create_text(40, 96, text="Type", font=(FONT, 9, "bold"), fill=TEXT, anchor="w")
        canvas.create_text(175, 96, text="Frequency", font=(FONT, 9, "bold"), fill=TEXT, anchor="w")
        canvas.create_text(355, 96, text="Length", font=(FONT, 9, "bold"), fill=TEXT, anchor="w")

        # ── 1. Custom Type Selector Box ──
        self.sound_val = config.get("sound", "Ping")
        type_box = _draw_rounded_polygon(canvas, 40, 112, 155, 146, r=8, fill=FIELD_BG, outline=FIELD_BD, width=1)
        type_txt = canvas.create_text(55, 129, text=self.sound_val, font=(FONT, 10), fill=TEXT, anchor="w")
        type_arrow = canvas.create_text(142, 129, text="▼", font=(FONT, 7), fill=TEXT, anchor="e")

        sound_menu = tk.Menu(win, tearoff=0, font=(FONT, 10), bg="white", fg=TEXT, activebackground=FIELD_BG, activeforeground=TEXT)
        for s in audio.available_sounds():
            def _select_sound(sel=s):
                self.sound_val = sel
                canvas.itemconfig(type_txt, text=sel)
                audio.play_sound(sel)
            sound_menu.add_command(label=s, command=_select_sound)

        def _open_sound_menu(_e):
            win.update_idletasks()
            sound_menu.tk_popup(win.winfo_rootx() + 40, win.winfo_rooty() + 148)

        for tag in (type_box, type_txt, type_arrow):
            canvas.tag_bind(tag, "<Button-1>", _open_sound_menu)
            canvas.tag_bind(tag, "<Enter>", lambda _e: canvas.config(cursor="hand2"))
            canvas.tag_bind(tag, "<Leave>", lambda _e: canvas.config(cursor=""))

        # ── 2. Frequency ── segmented HH:MM:SS entry
        self.work_seconds = config.get("work_seconds", 1200)
        _draw_rounded_polygon(canvas, 175, 112, 335, 146, r=8, fill=FIELD_BG, outline=FIELD_BD, width=1)
        self.freq_entry = _TimeEntry(win, seconds=self.work_seconds)
        canvas.create_window(255, 129, window=self.freq_entry, anchor="center")

        # ── 3. Length ── segmented HH:MM:SS entry
        self.break_seconds = config.get("break_seconds", 60)
        _draw_rounded_polygon(canvas, 355, 112, W-40, 146, r=8, fill=FIELD_BG, outline=FIELD_BD, width=1)
        self.len_entry = _TimeEntry(win, seconds=self.break_seconds)
        canvas.create_window(427, 129, window=self.len_entry, anchor="center")

        # Separator line
        canvas.create_line(40, 162, W-40, 162, fill="#cbe3ea", width=1)

        # ── Curved Title Field ──
        canvas.create_text(40, 180, text="Title", font=(FONT, 9, "bold"), fill=TEXT, anchor="w")
        _draw_rounded_polygon(canvas, 40, 196, W-40, 230, r=8, fill=FIELD_BG, outline=FIELD_BD, width=1)
        self.title_var = tk.StringVar(value=config.get("title", "Time for a break."))
        title_entry = tk.Entry(win, textvariable=self.title_var, font=(FONT, 10), bg=FIELD_BG, fg=TEXT, relief="flat", bd=0, highlightthickness=0)
        canvas.create_window(52, 213, window=title_entry, anchor="w", width=W-92)

        # ── Curved Message Field ──
        canvas.create_text(40, 246, text="Message", font=(FONT, 9, "bold"), fill=TEXT, anchor="w")
        _draw_rounded_polygon(canvas, 40, 262, W-40, 396, r=8, fill=FIELD_BG, outline=FIELD_BD, width=1)
        self.message_text = tk.Text(win, font=(FONT, 10), bg=FIELD_BG, fg=TEXT, relief="flat", bd=0, highlightthickness=0, wrap="word")
        self.message_text.insert("1.0", config.get("message", ""))
        canvas.create_window(52, 272, window=self.message_text, anchor="nw", width=W-92, height=112)

        # Center window
        win.update_idletasks()
        sw = win.winfo_screenwidth()
        sh = win.winfo_screenheight()
        x = (sw - W) // 2
        y = (sh - H) // 2
        win.geometry(f"{W}x{H}+{x}+{y}")
        win.protocol("WM_DELETE_WINDOW", self._on_close)

    def _save(self):
        new_config = dict(self._config)
        new_config["work_seconds"] = self.freq_entry.get_seconds() or self.work_seconds
        new_config["break_seconds"] = self.len_entry.get_seconds() or self.break_seconds
        new_config["title"] = self.title_var.get().strip() or "Time for a break."
        new_config["message"] = self.message_text.get("1.0", "end-1c").strip()
        new_config["sound"] = self.sound_val
        self.on_save(new_config)
        self._on_close()

    def _on_close(self):
        try:
            self.win.destroy()
        except tk.TclError:
            pass