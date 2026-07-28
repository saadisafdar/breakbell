"""
BreakBell - core application.

Waits `work_seconds` between breaks, then shows a centered on-screen
break card (countdown + progress bar + Cancel Break button), styled
after a teal "time for a break" notification design. Driven by a
config dict (see config.py) so settings can be changed live from the
Settings window without restarting the app.
"""

import tkinter as tk
import time

from . import audio
from . import tray
from .config import DEFAULT_CONFIG

NAVY = "#103046"
NAVY_DARK = "#0a2233"
NAVY_TRACK = "#2c5170"
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
        self.progress_bar_id = None
        self.time_label = None
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
            # A break is currently on screen - don't touch the auto-timer
            # now. Rescheduling here (even via _reschedule()'s own cancel
            # guard) would still schedule the next break using the full
            # delay counted from *now*, landing in the middle of or right
            # after the current break instead of after it properly ends.
            # end_break()/cancel_break() will reschedule correctly, using
            # the updated settings, once this break actually finishes.
            if was_enabled and not now_enabled:
                self._close_popup()
            return

        self._reschedule()
        if was_enabled and not now_enabled:
            self._close_popup()

    # ---------- scheduling ----------

    def _reschedule(self, delay_ms=None):
        # Always cancel any existing pending timer first. Without this,
        # calling _reschedule() twice (e.g. once from apply_config() while
        # a break is showing, and again from end_break() when it finishes)
        # leaves an orphaned timer alive that fires later on its own,
        # causing an unexpected extra break.
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
        """Safe entry point for manually starting a break (e.g. from the
        tray menu) - cancels the pending auto-scheduled timer first so it
        can't also fire later and cause a surprise second break."""
        if self.next_break_job is not None:
            try:
                self.root.after_cancel(self.next_break_job)
            except (ValueError, tk.TclError):
                pass
            self.next_break_job = None
        self.start_break()

    # ---------- break screen ----------

    def start_break(self):
        if self.popup is not None:
            try:
                self.popup.destroy()
            except tk.TclError:
                pass
        if self.overlay is not None:
            try:
                self.overlay.destroy()
            except tk.TclError:
                pass

        audio.play_sound(self.config.get("sound", "None"))

        self._break_active = True
        self._show_overlay()

        popup = tk.Toplevel(self.root)
        self.popup = popup
        popup.title("BreakBell")
        popup.attributes("-topmost", True)
        popup.overrideredirect(True)
        popup.configure(bg=NAVY)

        width = 440
        card = tk.Frame(popup, bg=NAVY, padx=26, pady=22)
        card.pack(fill="both", expand=True)

        content_row = tk.Frame(card, bg=NAVY)
        content_row.pack(fill="both", expand=True)

        left_col = tk.Frame(content_row, bg=NAVY)
        left_col.pack(side="left", fill="both", expand=True)

        right_col = tk.Frame(content_row, bg=NAVY)
        right_col.pack(side="right", padx=(24, 0))

        title = tk.Label(
            left_col, text=self.config.get("title", "Take a break"),
            font=("Segoe UI", 20, "bold"),
            bg=NAVY, fg=WHITE, anchor="w"
        )
        title.pack(anchor="w")

        body = tk.Frame(left_col, bg=NAVY)
        body.pack(anchor="w", pady=(18, 20), fill="x")
        for line in self.lines:
            tk.Label(
                body, text=line, font=("Segoe UI", 12), bg=NAVY, fg=WHITE, anchor="w"
            ).pack(anchor="w", pady=1)

        cancel_btn = tk.Button(
            left_col, text="Cancel Break", command=self.cancel_break,
            bg=WHITE, fg=NAVY_DARK, relief="flat", padx=12, pady=6,
            font=("Segoe UI", 9, "bold"), activebackground="#eafaf7",
            activeforeground=NAVY_DARK, cursor="hand2", bd=0
        )
        cancel_btn.pack(anchor="w")

        # Vertical progress bar: thick, fixed height, fills top-to-bottom and
        # drains (shrinks from the top, anchored at the bottom) as time passes
        vbar_width = 44
        vbar_height = 180
        bar_wrap = tk.Frame(right_col, bg=NAVY_TRACK, width=vbar_width, height=vbar_height)
        bar_wrap.pack()
        bar_wrap.pack_propagate(False)

        self.progress_canvas = tk.Canvas(
            bar_wrap, bg=NAVY_TRACK, width=vbar_width, height=vbar_height, highlightthickness=0
        )
        self.progress_canvas.pack(fill="both", expand=True)
        self.progress_bar_id = self.progress_canvas.create_rectangle(
            0, 0, vbar_width, vbar_height, fill=WHITE, width=0
        )
        self._vbar_width = vbar_width
        self._vbar_height = vbar_height

        break_seconds = self.config["break_seconds"]
        self.time_label = tk.Label(
            right_col, text=self._format_time(break_seconds),
            font=("Segoe UI", 11), bg=NAVY, fg=WHITE
        )
        self.time_label.pack(pady=(10, 0))

        popup.update_idletasks()
        height = card.winfo_reqheight()
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

        # Re-assert geometry: lift()/focus_force()/grab_set() can trigger Tk
        # to reprocess pack's automatic geometry request, silently resetting
        # position to (0,0) if we don't flush and reapply.
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.update_idletasks()

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
        # Absorb clicks so they don't reach whatever window is underneath
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

        self.time_label.config(text=self._format_time(remaining))
        frac = remaining / self._break_total
        try:
            filled_top = self._vbar_height * (1 - frac)
            self.progress_canvas.coords(
                self.progress_bar_id, 0, filled_top, self._vbar_width, self._vbar_height
            )
        except tk.TclError:
            return

        self.tick_job = self.root.after(200, self._tick)

    @staticmethod
    def _format_time(seconds):
        seconds = max(0, int(seconds))
        return f"{seconds // 60:02d}:{seconds % 60:02d}"

    def cancel_break(self):
        self._close_popup()
        self._reschedule()

    def end_break(self):
        self._close_popup()
        self._reschedule()

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