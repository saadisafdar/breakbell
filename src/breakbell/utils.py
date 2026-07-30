"""Shared drawing utilities for BreakBell canvas widgets."""


def _draw_rounded_polygon(canvas, x1, y1, x2, y2, r=10, **kwargs):
    """Draw a smooth rounded rectangle on a tk.Canvas and return its item ID."""
    points = [
        x1+r, y1,  x2-r, y1,  x2, y1,  x2, y1+r,
        x2, y2-r,  x2, y2,  x2-r, y2,  x1+r, y2,
        x1, y2,  x1, y2-r,  x1, y1+r,  x1, y1,
    ]
    return canvas.create_polygon(points, **kwargs, smooth=True)
