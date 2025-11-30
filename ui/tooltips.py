"""Reusable tooltip widget for Tkinter."""
from __future__ import annotations

import tkinter as tk


class Tooltip:
    """Simple tooltip implementation that appears near the target widget."""

    def __init__(self, widget: tk.Widget, text: str) -> None:
        self.widget = widget
        self.text = text
        self.tipwindow: tk.Toplevel | None = None
        widget.bind("<Enter>", self._show)
        widget.bind("<Leave>", self._hide)
        widget.bind("<FocusOut>", self._hide)

    def _show(self, _event: tk.Event | None = None) -> None:
        if self.tipwindow or not self.text:
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.tipwindow = tk.Toplevel(self.widget)
        self.tipwindow.wm_overrideredirect(True)
        self.tipwindow.wm_geometry(f"+{x}+{y}")
        label = tk.Label(
            self.tipwindow,
            text=self.text,
            justify=tk.LEFT,
            background="#ffffe0",
            relief=tk.SOLID,
            borderwidth=1,
            padx=6,
            pady=3,
            wraplength=260,
        )
        label.pack()

    def _hide(self, _event: tk.Event | None = None) -> None:
        if self.tipwindow is not None:
            self.tipwindow.destroy()
            self.tipwindow = None
