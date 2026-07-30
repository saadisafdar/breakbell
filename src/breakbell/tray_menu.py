"""Custom floating medium-sized rounded tray menu for BreakBell."""
import tkinter as tk

from .utils import _draw_rounded_polygon

FONT = "Segoe UI"
BG = "#ffffff"
BORDER = "#bce1ea"
TRANS_KEY = "#000001"
TEXT = "#1a1a1a"
TEAL = "#1F9FBC"
MUTED = "#527782"
HOVER_BG = "#eaf6f9"



class CustomTrayMenu:
    def __init__(self, root, on_settings, on_take_break, on_quit):
        self.root = root
        self.on_settings = on_settings
        self.on_take_break = on_take_break
        self.on_quit = on_quit
        self.win = None

    def show(self, x=None, y=None):
        if self.win is not None:
            try:
                self.win.destroy()
            except tk.TclError:
                pass

        win = tk.Toplevel(self.root)
        self.win = win
        win.title("BreakBell Menu")
        win.attributes("-topmost", True)
        win.overrideredirect(True)

        try:
            win.wm_attributes("-transparentcolor", TRANS_KEY)
            win.configure(bg=TRANS_KEY)
        except Exception:
            win.configure(bg=BG)

        W, H = 180, 110
        canvas = tk.Canvas(win, bg=TRANS_KEY, width=W, height=H, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Draw medium rounded white menu card with soft teal border
        _draw_rounded_polygon(canvas, 2, 2, W - 2, H - 2, r=12, fill=BG, outline=BORDER, width=1)

        items = [
            ("Settings", TEAL, "bold", self.on_settings),
            ("Take a break now", TEXT, "normal", self.on_take_break),
            ("Quit", MUTED, "normal", self.on_quit),
        ]

        curr_y = 8
        for i, (label, color, weight, cmd) in enumerate(items):
            item_h = 30
            rect = canvas.create_rectangle(8, curr_y, W - 8, curr_y + item_h, fill=BG, outline="")
            txt = canvas.create_text(20, curr_y + item_h // 2, text=label, font=(FONT, 9, weight), fill=color, anchor="w")

            def _click(_e, c=cmd):
                self.hide()
                self.root.after(10, c)

            def _hover(_e, r=rect):
                canvas.itemconfig(r, fill=HOVER_BG)
                canvas.config(cursor="hand2")

            def _leave(_e, r=rect):
                canvas.itemconfig(r, fill=BG)
                canvas.config(cursor="")

            for tag in (rect, txt):
                canvas.tag_bind(tag, "<Button-1>", _click)
                canvas.tag_bind(tag, "<Enter>", _hover)
                canvas.tag_bind(tag, "<Leave>", _leave)

            curr_y += item_h
            if i < len(items) - 1:
                canvas.create_line(12, curr_y, W - 12, curr_y, fill="#e2f0f4", width=1)

        win.update_idletasks()
        if x is None or y is None:
            px = win.winfo_pointerx()
            py = win.winfo_pointery()
            sw = win.winfo_screenwidth()
            sh = win.winfo_screenheight()

            x = max(10, min(px - W // 2, sw - W - 10))
            y = max(10, min(py - H - 10, sh - H - 40))

        win.geometry(f"{W}x{H}+{x}+{y}")
        win.lift()
        win.focus_force()
        win.bind("<FocusOut>", lambda _e: self.hide())

    def hide(self):
        if self.win is not None:
            try:
                self.win.destroy()
            except tk.TclError:
                pass
            self.win = None
