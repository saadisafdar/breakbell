"""Settings window for BreakBell - clean light theme matching reference design."""
import tkinter as tk
from tkinter import ttk

from . import audio
from . import tray
from . import updater

# ── Colour palette ──────────────────────────────────────────────────────────
BG          = "#e6f4f8"   # window background (soft freeze / ice teal tint)
CARD_BG     = "#ffffff"   # card / panel background
CARD_BORDER = "#b6e0eb"   # card border / separator
FIELD_BG    = "#f0f8fb"   # input field background (ice teal)
FIELD_BD    = "#aee0ed"   # input border
TEXT        = "#0b333d"   # primary text (dark cyan teal)
SUBTEXT     = "#4f7a86"   # muted / label text
ACCENT      = "#1F9FBC"   # save button / active accent (vivid break-window teal)
ACCENT_HV   = "#16839b"   # save button hover
TOGGLE_ON   = "#1F9FBC"   # toggle thumb colour when on
TOGGLE_OFF  = "#bdbdbd"
FONT        = "Segoe UI"


# ── Toggle switch widget ─────────────────────────────────────────────────────
class ToggleSwitch(tk.Canvas):
    """A pill-shaped on/off toggle rendered on a Canvas."""

    W, H, R = 46, 26, 13   # width, height, corner radius

    def __init__(self, parent, variable: tk.BooleanVar, **kw):
        kw.setdefault("bg", CARD_BG)
        kw.setdefault("highlightthickness", 0)
        super().__init__(parent, width=self.W, height=self.H, **kw)
        self._var = variable
        self._draw()
        self.bind("<Button-1>", self._toggle)
        variable.trace_add("write", lambda *_: self._draw())

    def _draw(self):
        self.delete("all")
        on = self._var.get()
        track = TOGGLE_ON if on else TOGGLE_OFF
        r = self.R

        # Pill track
        self.create_arc(0, 0, r*2, self.H, start=90, extent=180, fill=track, outline=track)
        self.create_arc(self.W - r*2, 0, self.W, self.H, start=270, extent=180, fill=track, outline=track)
        self.create_rectangle(r, 0, self.W - r, self.H, fill=track, outline=track)

        # Thumb
        pad = 3
        cx = self.W - r - pad if on else r + pad
        self.create_oval(cx - r + pad, pad, cx + r - pad, self.H - pad, fill="white", outline="white")

    def _toggle(self, _event=None):
        self._var.set(not self._var.get())


# ── HMS spinbox row ──────────────────────────────────────────────────────────
def _make_hms_widget(parent, total_seconds: int):
    """Returns a Frame containing HH h : MM m : SS s spinboxes plus a getter."""
    h, rem = divmod(int(total_seconds), 3600)
    m, s   = divmod(rem, 60)

    frame = tk.Frame(parent, bg=FIELD_BG, bd=1, relief="flat",
                     highlightbackground=FIELD_BD, highlightthickness=1)

    vars_ = []
    maxima = [23, 59, 59]
    initials = [h, m, s]
    suffixes = ["h", "m", "s"]

    for i, (init, maxi, suf) in enumerate(zip(initials, maxima, suffixes)):
        if i > 0:
            tk.Label(frame, text=":", bg=FIELD_BG, fg=SUBTEXT,
                     font=(FONT, 11, "bold")).pack(side="left", padx=(0, 2))

        var = tk.StringVar(value=f"{init:02d}")
        sb  = tk.Spinbox(
            frame, from_=0, to=maxi, width=2, textvariable=var,
            font=(FONT, 11), bg=FIELD_BG, fg=TEXT,
            buttonbackground=FIELD_BG, relief="flat",
            justify="center", insertbackground=TEXT,
            bd=0, highlightthickness=0
        )
        sb.pack(side="left", padx=(4, 0), pady=4)
        tk.Label(frame, text=suf, bg=FIELD_BG, fg=SUBTEXT,
                 font=(FONT, 10)).pack(side="left", padx=(1, 2))
        vars_.append(var)

    def get_seconds():
        try:
            return int(vars_[0].get()) * 3600 + int(vars_[1].get()) * 60 + int(vars_[2].get())
        except ValueError:
            return total_seconds

    return frame, get_seconds


# ── Helpers ──────────────────────────────────────────────────────────────────
def _label(parent, text, bold=False, size=10, color=TEXT, pady_top=0, pady_bot=5):
    weight = "bold" if bold else "normal"
    tk.Label(parent, text=text, font=(FONT, size, weight),
             bg=CARD_BG, fg=color, anchor="w"
             ).pack(anchor="w", pady=(pady_top, pady_bot))


def _section_label(parent, text):
    tk.Label(parent, text=text, font=(FONT, 11, "bold"),
             bg=CARD_BG, fg=TEXT, anchor="w").pack(anchor="w")


def _field_entry(parent, variable):
    wrapper = tk.Frame(parent, bg=FIELD_BG, bd=1, relief="flat",
                       highlightbackground=FIELD_BD, highlightthickness=1)
    wrapper.pack(fill="x", pady=(4, 0))
    tk.Entry(wrapper, textvariable=variable, font=(FONT, 11),
             bg=FIELD_BG, fg=TEXT, relief="flat",
             insertbackground=TEXT, bd=0, highlightthickness=0
             ).pack(fill="x", padx=8, pady=7)
    return wrapper


def _field_text(parent, height=4):
    wrapper = tk.Frame(parent, bg=FIELD_BG, bd=1, relief="flat",
                       highlightbackground=FIELD_BD, highlightthickness=1)
    wrapper.pack(fill="x", pady=(4, 0))
    txt = tk.Text(wrapper, height=height, font=(FONT, 11),
                  bg=FIELD_BG, fg=TEXT, relief="flat",
                  insertbackground=TEXT, wrap="word", bd=0, highlightthickness=0)
    txt.pack(fill="x", padx=8, pady=7)
    return wrapper, txt


# ── Settings window ──────────────────────────────────────────────────────────
class SettingsWindow:
    def __init__(self, root, config, on_save):
        self.on_save   = on_save
        self._config   = config

        self.win = tk.Toplevel(root)
        self.win.title("Settings")
        self.win.configure(bg=BG)
        self.win.resizable(False, False)
        self.win.attributes("-topmost", True)
        try:
            self._icon_img = tk.PhotoImage(file=tray.icon_path())
            self.win.iconphoto(True, self._icon_img)
        except Exception:
            pass

        # ── Scrollable canvas ──
        canvas  = tk.Canvas(self.win, bg=BG, highlightthickness=0)
        vscroll = tk.Scrollbar(self.win, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vscroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        vscroll.pack(side="right", fill="y")

        outer = tk.Frame(canvas, bg=BG, padx=20, pady=20)
        win_id = canvas.create_window((0, 0), window=outer, anchor="nw")

        outer.bind("<Configure>", lambda _e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.bind("<Configure>",  lambda  e: canvas.itemconfigure(win_id, width=e.width))

        def _scroll(event):
            if getattr(event, "num", None) == 4:
                canvas.yview_scroll(-1, "units")
            elif getattr(event, "num", None) == 5:
                canvas.yview_scroll(1, "units")
            else:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        canvas.bind_all("<MouseWheel>", _scroll)
        canvas.bind_all("<Button-4>",   _scroll)
        canvas.bind_all("<Button-5>",   _scroll)

        # ── Update banner (if available) ──
        up_info = updater.get_update_info()
        if up_info:
            banner = tk.Frame(outer, bg="#e3f2fd", padx=12, pady=8,
                              highlightbackground="#90caf9", highlightthickness=1)
            banner.pack(fill="x", pady=(0, 12))
            tk.Label(banner, text=f"🎉 Update available: v{up_info['version']}",
                     font=(FONT, 10, "bold"), bg="#e3f2fd", fg="#1565c0"
                     ).pack(side="left")
            tk.Button(banner, text="Download", command=updater.open_release_page,
                      bg=ACCENT, fg="white", relief="flat", padx=12, pady=4,
                      font=(FONT, 9, "bold"), activebackground=ACCENT_HV,
                      activeforeground="white", cursor="hand2", bd=0
                      ).pack(side="right")

        # ════════════════════════════════════════════════════════════════
        #  BREAKS card
        # ════════════════════════════════════════════════════════════════
        card = tk.Frame(outer, bg=CARD_BG, bd=1, relief="flat",
                        highlightbackground=CARD_BORDER, highlightthickness=1)
        card.pack(fill="x", pady=(0, 14))

        inner = tk.Frame(card, bg=CARD_BG, padx=18, pady=14)
        inner.pack(fill="x")

        # ── Breaks header row (title + Save/Cancel buttons) ──
        hdr = tk.Frame(inner, bg=CARD_BG)
        hdr.pack(fill="x", pady=(0, 14))

        tk.Label(hdr, text="Breaks", font=(FONT, 13, "bold"),
                 bg=CARD_BG, fg=TEXT).pack(side="left")

        tk.Button(hdr, text="Cancel", command=self._on_close,
                  bg=CARD_BG, fg=TEXT, relief="flat", padx=16, pady=5,
                  font=(FONT, 10), activebackground=FIELD_BD,
                  activeforeground=TEXT, cursor="hand2", bd=1
                  ).pack(side="right", padx=(8, 0))

        tk.Button(hdr, text="Save", command=self._save,
                  bg=ACCENT, fg="white", relief="flat", padx=20, pady=5,
                  font=(FONT, 10, "bold"), activebackground=ACCENT_HV,
                  activeforeground="white", cursor="hand2", bd=0
                  ).pack(side="right")

        self.enabled_var = tk.BooleanVar(value=config.get("enabled", True))

        # ── Separator ──
        tk.Frame(inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 14))

        # ── Type / Frequency / Length row ──
        row = tk.Frame(inner, bg=CARD_BG)
        row.pack(fill="x", pady=(0, 14))

        self._style_combobox()

        # Type column (Sound selection)
        type_col = tk.Frame(row, bg=CARD_BG)
        type_col.pack(side="left", padx=(0, 16))
        tk.Label(type_col, text="Type", font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 4))
        self.sound_var = tk.StringVar(value=config.get("sound", "Ping"))
        type_wrapper = tk.Frame(type_col, bg=FIELD_BG, bd=1, relief="flat",
                                highlightbackground=FIELD_BD, highlightthickness=1)
        type_wrapper.pack(anchor="w")
        type_cb = ttk.Combobox(type_wrapper, textvariable=self.sound_var,
                               values=audio.available_sounds(), state="readonly",
                               width=13, font=(FONT, 10))
        type_cb.pack(padx=6, pady=5)
        type_cb.bind("<<ComboboxSelected>>", lambda _e: audio.play_sound(self.sound_var.get()))

        # Frequency column
        freq_col = tk.Frame(row, bg=CARD_BG)
        freq_col.pack(side="left", padx=(0, 16))
        tk.Label(freq_col, text="Frequency", font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 4))
        freq_frame, self.get_work_seconds = _make_hms_widget(
            freq_col, config.get("work_seconds", 1200))
        freq_frame.pack(anchor="w")

        # Length column
        len_col = tk.Frame(row, bg=CARD_BG)
        len_col.pack(side="left")
        tk.Label(len_col, text="Length", font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=TEXT, anchor="w").pack(anchor="w", pady=(0, 4))
        len_frame, self.get_break_seconds = _make_hms_widget(
            len_col, config.get("break_seconds", 120))
        len_frame.pack(anchor="w")

        # ── Separator ──
        tk.Frame(inner, bg=CARD_BORDER, height=1).pack(fill="x", pady=(0, 14))

        # ── Title field ──
        tk.Label(inner, text="Title", font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=TEXT, anchor="w").pack(anchor="w")
        self.title_var = tk.StringVar(value=config.get("title", "Time for a break."))
        _field_entry(inner, self.title_var)

        # spacer
        tk.Frame(inner, bg=CARD_BG, height=12).pack()

        # ── Message field ──
        tk.Label(inner, text="Message", font=(FONT, 10, "bold"),
                 bg=CARD_BG, fg=TEXT, anchor="w").pack(anchor="w")
        _wrapper, self.message_text = _field_text(inner, height=4)
        self.message_text.insert("1.0", config.get("message", ""))


        # ── Size & position ──
        self.win.update_idletasks()
        cw = outer.winfo_reqwidth()
        ch = outer.winfo_reqheight()
        sw = self.win.winfo_screenwidth()
        sh = self.win.winfo_screenheight()

        width  = cw + vscroll.winfo_reqwidth() + 2
        height = min(ch, sh - 120)
        x = (sw - width) // 2
        y = (sh - height) // 2
        self.win.geometry(f"{width}x{height}+{x}+{y}")
        self.win.update_idletasks()
        self.win.minsize(min(width, 440), 320)


        self.win.protocol("WM_DELETE_WINDOW", self._on_close)


    # ── Helpers ──────────────────────────────────────────────────────────────

    def _style_combobox(self):
        style = ttk.Style()
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TCombobox",
                         fieldbackground=FIELD_BG, background=FIELD_BG,
                         foreground=TEXT, arrowcolor=SUBTEXT,
                         bordercolor=FIELD_BD, lightcolor=FIELD_BG,
                         darkcolor=FIELD_BG, selectbackground=FIELD_BG,
                         selectforeground=TEXT)
        style.map("TCombobox",
                  fieldbackground=[("readonly", FIELD_BG)],
                  selectbackground=[("readonly", ACCENT)],
                  selectforeground=[("readonly", "white")])



    def _on_close(self):
        try:
            self.win.unbind_all("<MouseWheel>")
            self.win.unbind_all("<Button-4>")
            self.win.unbind_all("<Button-5>")
        except tk.TclError:
            pass
        self.win.destroy()

    def _save(self):
        new_config = {
            "enabled":      self.enabled_var.get(),
            "work_seconds": max(1, self.get_work_seconds()),
            "break_seconds": max(1, self.get_break_seconds()),
            "title":        self.title_var.get().strip() or "Time for a break.",
            "message":      self.message_text.get("1.0", "end").strip(),
            "sound":        self.sound_var.get(),
        }
        self._on_close()
        self.on_save(new_config)