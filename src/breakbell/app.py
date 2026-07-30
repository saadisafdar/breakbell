"""
BreakBell - core application.

Waits `work_seconds` between breaks, then shows a centered on-screen
break card (countdown + progress bar + Cancel Break button), styled
after a teal "time for a break" notification design. Driven by a
config dict (see config.py) so settings can be changed live from the
Settings window without restarting the app.
"""

import time
import tkinter as tk

from . import audio
from . import tray
from .config import DEFAULT_CONFIG
from .utils import _draw_rounded_polygon

TEAL = "#1F9FBC"
TEAL_DARK = "#0c2b33"
TEAL_TRACK = "#164956"
WHITE = "#ffffff"


class BreakTimerApp:
    def __init__(self, config=None):
        self.config = dict(DEFAULT_CONFIG)
        if config:
            self.config.update(config)

        self.root = tk.Tk()
        self.root.withdraw()  # main window is never shown
        try:
            self._icon_img = tk.PhotoImage(file=tray.icon_path())
            self.root.iconphoto(True, self._icon_img)
        except Exception:
            pass

        self.popup = None
        self.overlay = None
        self.progress_canvas = None
        self.time_label_id = None
        self.break_end_time = None
        self.tick_job = None
        self.next_break_job = None
        self.refocus_job = None
        self._break_active = False

        self.root.protocol("WM_DELETE_WINDOW", self.root.destroy)
        self._reschedule()

    # ---------- config ----------

    @property
    def lines(self):
        return [l for l in self.config["message"].split("\n") if l.strip()] or [""]

    def apply_config(self, new_config):
        """Called from the Settings window. Applies changes immediately."""
        was_enabled = self.config.get("enabled", True)
        self.config.update(new_config)
        now_enabled = self.config.get("enabled", True)

        if self._break_active:
            if was_enabled and not now_enabled:
                self._close_popup()
            return

        self._reschedule()
        if was_enabled and not now_enabled:
            self._close_popup()

    # ---------- scheduling ----------

    def _reschedule(self, delay_ms=None):
        if self.next_break_job is not None:
            try:
                self.root.after_cancel(self.next_break_job)
            except (ValueError, tk.TclError):
                pass
            self.next_break_job = None

        if not self.config.get("enabled", True):
            return
        if delay_ms is None:
            delay_ms = int(self.config["work_seconds"] * 1000)
        self.next_break_job = self.root.after(delay_ms, self.start_break)

    def trigger_break_now(self):
        if self.next_break_job is not None:
            try:
                self.root.after_cancel(self.next_break_job)
            except (ValueError, tk.TclError):
                pass
            self.next_break_job = None
        self.start_break()

    # ---------- break screen ----------

    def start_break(self):
        # Use _close_popup() so _break_active is properly reset before we
        # re-enter, preventing any desync if start_break() is called while
        # a break is already in progress.
        if self.popup is not None or self.overlay is not None:
            self._close_popup()

        audio.play_sound(self.config.get("sound", "None"))

        self._break_active = True
        self._show_overlay()

        popup = tk.Toplevel(self.root)
        self.popup = popup
        popup.title("BreakBell")
        popup.attributes("-topmost", True)
        popup.overrideredirect(True)

        TRANS_KEY = "#000001"
        try:
            popup.wm_attributes("-transparentcolor", TRANS_KEY)
            popup.configure(bg=TRANS_KEY)
        except Exception:
            popup.configure(bg=TEAL)

        width, height = 460, 220
        canvas = tk.Canvas(popup, bg=TRANS_KEY, width=width, height=height, highlightthickness=0)
        canvas.pack(fill="both", expand=True)

        # Smooth rounded teal card background
        _draw_rounded_polygon(canvas, 4, 4, width - 4, height - 4, r=24, fill=TEAL, outline="")

        # Title
        canvas.create_text(30, 42, text=self.config.get("title", "Time for a break."),
                           font=("Segoe UI", 20, "bold"), fill=WHITE, anchor="w")

        # Message
        msg_str = "\n".join(self.lines)
        canvas.create_text(30, 105, text=msg_str,
                           font=("Segoe UI", 11), fill=WHITE, anchor="w", justify="left")

        # Rounded Cancel Break Button
        btn_bg = _draw_rounded_polygon(canvas, 30, 156, 165, 192, r=8, fill=WHITE, outline="")
        btn_txt = canvas.create_text(97, 174, text="Cancel Break", font=("Segoe UI", 9, "bold"), fill=TEAL_DARK)

        for item in (btn_bg, btn_txt):
            canvas.tag_bind(item, "<Button-1>", lambda _e: self.cancel_break())
            canvas.tag_bind(item, "<Enter>", lambda _e: canvas.config(cursor="hand2"))
            canvas.tag_bind(item, "<Leave>", lambda _e: canvas.config(cursor=""))

        # Vertical Progress Bar (Right side)
        vbar_w, vbar_h = 44, 150
        vx1, vy1 = 380, 24
        vx2, vy2 = vx1 + vbar_w, vy1 + vbar_h

        # Rounded container
        _draw_rounded_polygon(canvas, vx1, vy1, vx2, vy2, r=12, fill=TEAL_TRACK, outline="")

        self.progress_canvas = canvas
        self._vbar_vx1 = vx1
        self._vbar_vy1 = vy1
        self._vbar_vx2 = vx2
        self._vbar_vy2 = vy2
        self._vbar_height = vbar_h

        break_seconds = self.config["break_seconds"]
        self._bar_fill_id = _draw_rounded_polygon(canvas, vx1, vy1, vx2, vy2, r=12, fill=WHITE, outline="")

        # Timer text below bar
        self.time_label_id = canvas.create_text(vx1 + vbar_w // 2, vy2 + 18,
                                                     text=self._format_time(break_seconds),
                                                     font=("Segoe UI", 11, "bold"), fill=WHITE)

        popup.update_idletasks()
        screen_w = popup.winfo_screenwidth()
        screen_h = popup.winfo_screenheight()
        x = (screen_w - width) // 2
        y = (screen_h - height) // 2
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.update_idletasks()

        self.overlay.lift()
        popup.lift()
        popup.focus_force()
        try:
            popup.grab_set()
        except tk.TclError:
            pass
        popup.bind("<FocusOut>", self._on_break_focus_out)

        self._break_total = break_seconds
        self.break_end_time = time.monotonic() + break_seconds
        self._tick()

    def _show_overlay(self):
        overlay = tk.Toplevel(self.root)
        self.overlay = overlay
        overlay.overrideredirect(True)
        overlay.attributes("-topmost", True)
        try:
            overlay.attributes("-alpha", 0.55)
        except tk.TclError:
            pass
        overlay.configure(bg="#000000")
        overlay.geometry(
            f"{overlay.winfo_screenwidth()}x{overlay.winfo_screenheight()}+0+0"
        )
        overlay.bind("<Button-1>", lambda e: "break")

    def _on_break_focus_out(self, _event=None):
        if not self._break_active or self.popup is None:
            return
        if self.refocus_job is not None:
            try:
                self.root.after_cancel(self.refocus_job)
            except (ValueError, tk.TclError):
                pass
        self.refocus_job = self.root.after(400, self._regain_focus)

    def _regain_focus(self):
        self.refocus_job = None
        if not self._break_active or self.popup is None:
            return
        try:
            if self.overlay is not None:
                self.overlay.lift()
            self.popup.lift()
            self.popup.focus_force()
        except tk.TclError:
            pass

    def _tick(self):
        remaining = self.break_end_time - time.monotonic()
        if remaining <= 0 or self.popup is None:
            self.end_break()
            return

        try:
            self.progress_canvas.itemconfig(self.time_label_id, text=self._format_time(remaining))
            frac = max(0.0, min(1.0, remaining / self._break_total))
            filled_top = self._vbar_vy1 + (self._vbar_height * (1 - frac))

            self.progress_canvas.delete(self._bar_fill_id)
            if frac > 0:
                h_diff = self._vbar_vy2 - filled_top
                r_val = min(12, max(2, int(h_diff / 2)))
                self._bar_fill_id = _draw_rounded_polygon(
                    self.progress_canvas,
                    self._vbar_vx1, int(filled_top),
                    self._vbar_vx2, self._vbar_vy2,
                    r=r_val, fill=WHITE, outline=""
                )
        except (tk.TclError, AttributeError):
            return

        self.tick_job = self.root.after(200, self._tick)

    @staticmethod
    def _format_time(seconds):
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def _finish_break(self):
        """Shared logic for both cancelling and naturally ending a break."""
        self._close_popup()
        self._reschedule()

    def cancel_break(self):
        self._finish_break()

    def end_break(self):
        self._finish_break()

    def _close_popup(self):
        self._break_active = False
        if self.refocus_job is not None:
            try:
                self.root.after_cancel(self.refocus_job)
            except (ValueError, tk.TclError):
                pass
            self.refocus_job = None
        if self.tick_job is not None:
            try:
                self.root.after_cancel(self.tick_job)
            except (ValueError, tk.TclError):
                pass
            self.tick_job = None
        if self.popup is not None:
            try:
                self.popup.grab_release()
            except tk.TclError:
                pass
            try:
                self.popup.destroy()
            except tk.TclError:
                pass
            self.popup = None
        if self.overlay is not None:
            try:
                self.overlay.destroy()
            except tk.TclError:
                pass
            self.overlay = None

    def run(self):
        self.root.mainloop()