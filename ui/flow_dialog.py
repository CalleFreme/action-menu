"""Dialog helpers for Action Menu UI."""
from __future__ import annotations

from typing import Iterable, List
import tkinter as tk
from tkinter import ttk


class FlowCaptureDialog(tk.Toplevel):
    """Collects post-session flow + emotion reflections."""

    def __init__(
        self,
        parent: tk.Widget,
        *,
        activity: str,
        flow_before: int,
        emotion_before: str,
        emotions: Iterable[str],
    ) -> None:
        super().__init__(parent)
        self.result: dict[str, int | str] | None = None
        self._emotions: List[str] = list(emotions)

        self.title("Flow + emotion checkout")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        self.protocol("WM_DELETE_WINDOW", self._skip)

        container = ttk.Frame(self, padding=16)
        container.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text=f"How did '{activity}' feel?").pack(anchor=tk.W)
        ttk.Label(
            container,
            text=f"Flow before: {flow_before}/5 · Emotion before: {emotion_before}",
        ).pack(anchor=tk.W, pady=(0, 8))

        ttk.Label(container, text="Flow after (1-5)").pack(anchor=tk.W)
        self.flow_scale = tk.Scale(container, from_=1, to=5, orient=tk.HORIZONTAL, length=220)
        self.flow_scale.set(flow_before)
        self.flow_scale.pack(fill=tk.X)

        ttk.Label(container, text="Emotion after session").pack(anchor=tk.W, pady=(10, 0))
        default_emotion = emotion_before if emotion_before in self._emotions else (self._emotions[0] if self._emotions else "")
        self.emotion_var = tk.StringVar(value=default_emotion)
        ttk.Combobox(container, values=self._emotions, textvariable=self.emotion_var, state="readonly").pack(fill=tk.X)

        ttk.Label(container, text="What is this feeling communicating?").pack(anchor=tk.W, pady=(10, 0))
        self.message_text = tk.Text(container, height=3, wrap=tk.WORD)
        self.message_text.pack(fill=tk.BOTH, expand=True)

        ttk.Label(container, text="What is it motivating you to do?").pack(anchor=tk.W, pady=(10, 0))
        self.motivation_text = tk.Text(container, height=3, wrap=tk.WORD)
        self.motivation_text.pack(fill=tk.BOTH, expand=True)

        actions = ttk.Frame(container)
        actions.pack(fill=tk.X, pady=(12, 0))
        ttk.Button(actions, text="Save log", command=self._save).pack(side=tk.RIGHT)
        ttk.Button(actions, text="Skip", command=self._skip).pack(side=tk.RIGHT, padx=(0, 8))

    def _save(self) -> None:
        self.result = {
            "flow_after": int(self.flow_scale.get()),
            "emotion_after": self.emotion_var.get(),
            "message": self.message_text.get("1.0", tk.END).strip(),
            "motivation": self.motivation_text.get("1.0", tk.END).strip(),
        }
        self.destroy()

    def _skip(self) -> None:
        self.result = None
        self.destroy()
