"""Tkinter-based Action Menu prototype with persistence and journaling."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Dict, List
import tkinter as tk
from tkinter import messagebox, simpledialog, ttk

from models import (
    FlowLog,
    HabitPlan,
    JournalEntry,
    JournalSuggestion,
    QuickCaptureItem,
    SmartGoal,
    TimeEntry,
)
from storage import StorageManager, get_default_store_path
from journal_ai import extract_suggestions

CATEGORY_OPTIONS = ["General", "Creative", "Startup", "Learning", "Body", "Recovery"]
CATEGORY_COLORS: Dict[str, str] = {
    "General": "#7a7a7a",
    "Creative": "#ee8130",
    "Startup": "#0078d4",
    "Learning": "#7357ff",
    "Body": "#2e8b57",
    "Recovery": "#c55bff",
}
EMOTIONS = [
    "Calm",
    "Curious",
    "Confident",
    "Energized",
    "Bored",
    "Anxious",
    "Tired",
    "Stuck",
    "Excited",
]
QUICK_CAPTURE_STATUSES = ["Inbox", "Today", "Later", "Archived"]


class ActionMenuApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Action Menu")
        self.geometry("1280x840")
        self.minsize(1100, 780)

        store_path = get_default_store_path()
        self.storage = StorageManager(store_path)
        self.state = self.storage.load()

        self.timer_start: datetime | None = None
        self.pending_flow_context: Dict[str, int | str] | None = None
        self.current_suggestions: List[JournalSuggestion] = []
        self.flow_dialog: tk.Toplevel | None = None

        self._build_style()
        self._build_layout()
        self._hydrate_all()

    # region build layout
    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subheader.TLabel", font=("Segoe UI", 12))
        style.configure("Card.TLabelframe", padding=12)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 12, "bold"))
        style.configure("Accent.TButton", padding=6)

    def _build_layout(self) -> None:
        header = ttk.Frame(self, padding=20)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Action Menu", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header,
            text=(
                "Design your week around what matters: clarify values, craft SMART goals, "
                "install habits, plan actions, journal discoveries, and track the hours that move the needle."
            ),
            style="Subheader.TLabel",
            wraplength=1000,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(6, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        notebook.add(self._build_vision_tab(notebook), text="North Star")
        notebook.add(self._build_goals_tab(notebook), text="SMART Goals")
        notebook.add(self._build_habits_tab(notebook), text="Habits & Actions")
        notebook.add(self._build_weekly_tab(notebook), text="Weekly Menu")
        notebook.add(self._build_time_tab(notebook), text="Time & Flow")
        notebook.add(self._build_journal_tab(notebook), text="Journal")
        notebook.add(self._build_quick_capture_tab(notebook), text="Quick Capture")
        notebook.add(self._build_integrations_tab(notebook), text="Integrations")

    def _build_vision_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        prompts = (
            "Why do these ambitions matter deeply?",
            "What would a wildly successful week look like?",
            "What experiments prove I'm living authentically?",
        )
        ttk.Label(tab, text="Authentic Life Prompts", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        prompt_box = tk.Text(tab, height=5, wrap=tk.WORD)
        prompt_box.insert(tk.END, "\n".join(f"• {p}" for p in prompts))
        prompt_box.configure(state=tk.DISABLED, bg="#f8f8f8", relief=tk.FLAT)
        prompt_box.pack(fill=tk.X, pady=(6, 12))

        input_frame = ttk.Frame(tab)
        input_frame.pack(fill=tk.BOTH, expand=True)

        self.values_text = self._add_labeled_text(input_frame, "Values & Why it matters", 0)
        self.milestones_text = self._add_labeled_text(input_frame, "Milestones for next 12 months", 1)
        self.energy_text = self._add_labeled_text(input_frame, "Energy / Recovery rituals", 2)

        ttk.Button(tab, text="Commit Intentions", command=self._commit_intentions, style="Accent.TButton").pack(
            anchor=tk.E, pady=10
        )
        return tab

    def _add_labeled_text(self, parent: ttk.Frame, label: str, column: int, *, height: int = 8) -> tk.Text:
        frame = ttk.Labelframe(parent, text=label, style="Card.TLabelframe")
        frame.grid(row=0, column=column, sticky="nsew", padx=6)
        parent.columnconfigure(column, weight=1)
        widget = tk.Text(frame, height=height, wrap=tk.WORD)
        widget.pack(fill=tk.BOTH, expand=True)
        return widget

    def _build_goals_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        form = ttk.Labelframe(tab, text="Define a SMART goal", style="Card.TLabelframe")
        form.pack(fill=tk.X)

        self.goal_vars: Dict[str, tk.Entry] = {}
        fields = [
            ("Title", "title"),
            ("Specific", "specific"),
            ("Measurable", "measurable"),
            ("Achievable", "achievable"),
            ("Relevant", "relevant"),
            ("Time-bound", "time_bound"),
        ]
        for idx, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=idx, column=0, sticky=tk.W, pady=3)
            entry = ttk.Entry(form)
            entry.grid(row=idx, column=1, sticky=tk.EW, padx=6, pady=3)
            self.goal_vars[key] = entry
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Horizon").grid(row=len(fields), column=0, sticky=tk.W, pady=3)
        self.goal_horizon = ttk.Combobox(form, values=["Today", "This Week", "This Month", "Long Term"], state="readonly")
        self.goal_horizon.current(3)
        self.goal_horizon.grid(row=len(fields), column=1, sticky=tk.EW, padx=6, pady=3)

        ttk.Label(form, text="Category").grid(row=len(fields) + 1, column=0, sticky=tk.W, pady=3)
        self.goal_category = ttk.Combobox(form, values=CATEGORY_OPTIONS, state="readonly")
        self.goal_category.current(0)
        self.goal_category.grid(row=len(fields) + 1, column=1, sticky=tk.EW, padx=6, pady=3)

        ttk.Button(form, text="Add goal", command=self._add_goal).grid(row=len(fields) + 2, column=1, sticky=tk.E, pady=8)

        self.goal_tree = ttk.Treeview(
            tab,
            columns=("title", "category", "horizon", "measure"),
            show="headings",
            height=10,
        )
        for col, label in zip(
            ("title", "category", "horizon", "measure"),
            ("Goal", "Category", "Horizon", "Key Metric"),
        ):
            self.goal_tree.heading(col, text=label)
            anchor = tk.CENTER if col in {"category", "horizon"} else tk.W
            width = 120 if col != "title" else 320
            self.goal_tree.column(col, anchor=anchor, width=width)
        self.goal_tree.pack(fill=tk.BOTH, expand=True, pady=12)

        return tab

    def _build_habits_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        form = ttk.Labelframe(tab, text="Habit design (cue → action → celebrate)", style="Card.TLabelframe")
        form.pack(fill=tk.X)

        self.habit_entries: Dict[str, ttk.Entry] = {}
        fields = [
            ("Habit name", "name"),
            ("Anchor / trigger", "anchor"),
            ("Frequency", "frequency"),
            ("Success metric", "success_metric"),
        ]
        for idx, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=idx, column=0, sticky=tk.W, pady=3)
            entry = ttk.Entry(form)
            entry.grid(row=idx, column=1, sticky=tk.EW, padx=6, pady=3)
            self.habit_entries[key] = entry
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Linked goal").grid(row=len(fields), column=0, sticky=tk.W, pady=3)
        self.habit_goal = ttk.Combobox(form, values=[], state="readonly")
        self.habit_goal.grid(row=len(fields), column=1, sticky=tk.EW, padx=6, pady=3)

        ttk.Button(form, text="Add habit", command=self._add_habit).grid(row=len(fields) + 1, column=1, sticky=tk.E, pady=8)

        self.habit_tree = ttk.Treeview(
            tab,
            columns=("name", "frequency", "anchor", "goal"),
            show="headings",
            height=9,
        )
        for col, label in zip(("name", "frequency", "anchor", "goal"), ("Habit", "Frequency", "Anchor", "Goal")):
            self.habit_tree.heading(col, text=label)
            self.habit_tree.column(col, anchor=tk.W, width=150)
        self.habit_tree.pack(fill=tk.BOTH, expand=True, pady=12)

        ttk.Label(tab, text="Micro-actions spawned by habits:").pack(anchor=tk.W)
        self.action_list = tk.Listbox(tab, height=5)
        self.action_list.pack(fill=tk.X, pady=(6, 0))

        return tab

    def _build_weekly_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        form = ttk.Labelframe(tab, text="Weekly action generator", style="Card.TLabelframe")
        form.pack(fill=tk.X)

        ttk.Label(form, text="Action description").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.action_entry = ttk.Entry(form)
        self.action_entry.grid(row=0, column=1, sticky=tk.EW, padx=6, pady=3)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Timeframe").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.action_timeframe = ttk.Combobox(form, values=list(self.state.weekly_actions.keys()), state="readonly")
        self.action_timeframe.current(0)
        self.action_timeframe.grid(row=1, column=1, sticky=tk.EW, padx=6, pady=3)

        ttk.Label(form, text="Motivation (goal / habit)").grid(row=2, column=0, sticky=tk.W, pady=3)
        self.action_motivation = ttk.Combobox(form, state="readonly")
        self.action_motivation.grid(row=2, column=1, sticky=tk.EW, padx=6, pady=3)

        ttk.Button(form, text="Add to weekly menu", command=self._add_weekly_action).grid(row=3, column=1, sticky=tk.E, pady=8)

        board = ttk.Frame(tab)
        board.pack(fill=tk.BOTH, expand=True, pady=12)
        board.columnconfigure((0, 1, 2), weight=1)

        self.week_lists: Dict[str, tk.Listbox] = {}
        for idx, bucket in enumerate(self.state.weekly_actions):
            frame = ttk.Labelframe(board, text=bucket, padding=6)
            frame.grid(row=0, column=idx, sticky="nsew", padx=6)
            listbox = tk.Listbox(frame, height=12)
            listbox.pack(fill=tk.BOTH, expand=True)
            self.week_lists[bucket] = listbox

        ttk.Label(tab, text="Today Focus (pick three)").pack(anchor=tk.W, pady=(6, 0))
        self.today_focus = tk.Listbox(tab, height=4)
        self.today_focus.pack(fill=tk.X, pady=6)

        ttk.Button(tab, text="Send top items to Today", command=self._send_focus_to_today).pack(anchor=tk.E)

        return tab

    def _build_time_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        form = ttk.Labelframe(tab, text="Deep work timer", style="Card.TLabelframe")
        form.pack(fill=tk.X)

        ttk.Label(form, text="Activity / experiment").grid(row=0, column=0, sticky=tk.W, pady=3)
        self.timer_activity = ttk.Entry(form)
        self.timer_activity.grid(row=0, column=1, sticky=tk.EW, padx=6, pady=3)
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Category").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.timer_category = ttk.Combobox(
            form,
            values=["Creative", "Learning", "Shipping", "Body", "Recovery"],
            state="readonly",
        )
        self.timer_category.current(0)
        self.timer_category.grid(row=1, column=1, sticky=tk.EW, padx=6, pady=3)

        mood_frame = ttk.Frame(form)
        mood_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=6)
        ttk.Label(mood_frame, text="Flow before block (1-5)").grid(row=0, column=0, sticky=tk.W)
        self.flow_before_var = tk.IntVar(value=3)
        ttk.Scale(mood_frame, from_=1, to=5, orient=tk.HORIZONTAL, variable=self.flow_before_var).grid(
            row=0, column=1, sticky=tk.EW, padx=6
        )
        mood_frame.columnconfigure(1, weight=1)
        ttk.Label(mood_frame, text="Emotion right now").grid(row=1, column=0, sticky=tk.W, pady=3)
        self.emotion_before_var = tk.StringVar(value=EMOTIONS[0])
        ttk.Combobox(mood_frame, values=EMOTIONS, textvariable=self.emotion_before_var, state="readonly").grid(
            row=1, column=1, sticky=tk.EW, padx=6
        )

        button_frame = ttk.Frame(form)
        button_frame.grid(row=3, column=0, columnspan=2, pady=6)
        ttk.Button(button_frame, text="Start", command=self._start_timer).grid(row=0, column=0, padx=6)
        ttk.Button(button_frame, text="Stop & log", command=self._stop_timer).grid(row=0, column=1, padx=6)
        ttk.Button(button_frame, text="Manual log", command=self._manual_time_entry).grid(row=0, column=2, padx=6)

        self.timer_status = tk.StringVar(value="Timer idle")
        ttk.Label(tab, textvariable=self.timer_status, foreground="#0078d4").pack(anchor=tk.W, pady=(10, 0))

        self.time_tree = ttk.Treeview(
            tab,
            columns=("activity", "category", "start", "duration", "color"),
            show="headings",
            height=10,
        )
        for col, label in zip(
            ("activity", "category", "start", "duration", "color"),
            ("Activity", "Category", "Start", "Hours", "Calendar tag"),
        ):
            anchor = tk.CENTER if col in {"category", "duration", "color"} else tk.W
            width = 120 if col not in {"activity", "color"} else (260 if col == "activity" else 140)
            self.time_tree.heading(col, text=label)
            self.time_tree.column(col, anchor=anchor, width=width)
        self.time_tree.pack(fill=tk.BOTH, expand=True, pady=12)

        self.effort_summary = tk.StringVar(value="No hours tracked yet.")
        ttk.Label(tab, textvariable=self.effort_summary, wraplength=900).pack(anchor=tk.W)

        self.flow_summary = tk.StringVar(value="Flow data pending first log.")
        ttk.Label(tab, textvariable=self.flow_summary, wraplength=900).pack(anchor=tk.W, pady=(4, 0))

        self.flow_log_tree = ttk.Treeview(
            tab,
            columns=("activity", "before", "after", "emotion", "created"),
            show="headings",
            height=6,
        )
        for col, label in zip(
            ("activity", "before", "after", "emotion", "created"),
            ("Block", "Flow before", "Flow after", "Emotion after", "Logged"),
        ):
            anchor = tk.CENTER if col != "activity" else tk.W
            width = 120 if col != "activity" else 240
            self.flow_log_tree.heading(col, text=label)
            self.flow_log_tree.column(col, anchor=anchor, width=width)
        self.flow_log_tree.pack(fill=tk.BOTH, expand=True, pady=(6, 0))

        return tab

    def _build_journal_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        editor = ttk.Frame(tab)
        editor.pack(fill=tk.BOTH, expand=True)
        editor.columnconfigure(0, weight=2)
        editor.columnconfigure(1, weight=1)

        left = ttk.Frame(editor)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        ttk.Label(left, text="Daily journal (What happened today, anyway?)").pack(anchor=tk.W)
        self.journal_text = tk.Text(left, height=12, wrap=tk.WORD)
        self.journal_text.pack(fill=tk.BOTH, expand=True, pady=6)
        self.journal_text.bind("<KeyRelease>", lambda _event: self._update_journal_suggestions())
        ttk.Button(left, text="Save entry", command=self._save_journal_entry, style="Accent.TButton").pack(anchor=tk.E)

        right = ttk.Frame(editor)
        right.grid(row=0, column=1, sticky="nsew")
        ttk.Label(right, text="Actionable suggestions").pack(anchor=tk.W)
        self.journal_suggestions = tk.Listbox(right, height=6)
        self.journal_suggestions.pack(fill=tk.X, pady=4)

        btns = ttk.Frame(right)
        btns.pack(fill=tk.X, pady=(4, 10))
        ttk.Button(btns, text="Add to Today", command=self._suggestion_to_today).grid(row=0, column=0, padx=4)
        ttk.Button(btns, text="Draft goal", command=self._suggestion_to_goal).grid(row=0, column=1, padx=4)
        ttk.Button(btns, text="Draft habit", command=self._suggestion_to_habit).grid(row=0, column=2, padx=4)
        ttk.Button(btns, text="Quick capture", command=self._suggestion_to_capture).grid(row=0, column=3, padx=4)

        ttk.Label(right, text="Journal history").pack(anchor=tk.W)
        self.journal_history = ttk.Treeview(
            right,
            columns=("timestamp", "excerpt"),
            show="headings",
            height=8,
        )
        self.journal_history.heading("timestamp", text="Captured")
        self.journal_history.heading("excerpt", text="Excerpt")
        self.journal_history.column("timestamp", width=140, anchor=tk.CENTER)
        self.journal_history.column("excerpt", width=240, anchor=tk.W)
        self.journal_history.pack(fill=tk.BOTH, expand=True)
        self.journal_history.bind("<<TreeviewSelect>>", self._on_journal_select)

        self.journal_detail = tk.Text(tab, height=6, wrap=tk.WORD)
        self.journal_detail.configure(state=tk.DISABLED)
        self.journal_detail.pack(fill=tk.X, pady=(10, 0))

        self._update_journal_suggestions()

        return tab

    def _build_quick_capture_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        entry_frame = ttk.Frame(tab)
        entry_frame.pack(fill=tk.X)
        ttk.Label(entry_frame, text="Drop a thought, task, or idea:").grid(row=0, column=0, sticky=tk.W)
        self.quick_entry = ttk.Entry(entry_frame)
        self.quick_entry.grid(row=0, column=1, sticky=tk.EW, padx=6)
        entry_frame.columnconfigure(1, weight=1)
        ttk.Button(entry_frame, text="Capture", command=self._add_quick_item).grid(row=0, column=2)

        ttk.Label(tab, text="Inbox → Today → Later → Archived").pack(anchor=tk.W, pady=(10, 0))
        self.quick_tree = ttk.Treeview(
            tab,
            columns=("text", "status", "created"),
            show="headings",
            height=12,
        )
        self.quick_tree.heading("text", text="Item")
        self.quick_tree.heading("status", text="Status")
        self.quick_tree.heading("created", text="Captured")
        self.quick_tree.column("text", width=360, anchor=tk.W)
        self.quick_tree.column("status", width=100, anchor=tk.CENTER)
        self.quick_tree.column("created", width=140, anchor=tk.CENTER)
        self.quick_tree.pack(fill=tk.BOTH, expand=True, pady=8)

        action_bar = ttk.Frame(tab)
        action_bar.pack(fill=tk.X)
        ttk.Button(action_bar, text="Pin to Today", command=lambda: self._update_quick_status("Today")).grid(row=0, column=0, padx=4)
        ttk.Button(action_bar, text="Schedule Later", command=lambda: self._update_quick_status("Later")).grid(row=0, column=1, padx=4)
        ttk.Button(action_bar, text="Archive", command=lambda: self._update_quick_status("Archived")).grid(row=0, column=2, padx=4)
        ttk.Button(action_bar, text="Delete", command=self._delete_quick_item).grid(row=0, column=3, padx=4)

        self.quick_status_msg = tk.StringVar(value="")
        ttk.Label(tab, textvariable=self.quick_status_msg, foreground="#0078d4").pack(anchor=tk.W)

        return tab

    def _build_integrations_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        ttk.Label(tab, text="Prototype integrations", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        info = (
            "Export weekly plan to Google Calendar",
            "Sync time blocks with wearable or health data",
            "Push habit reminders via email or mobile notifications",
        )
        ttk.Label(tab, text="\n".join(f"• {line}" for line in info)).pack(anchor=tk.W, pady=10)

        ttk.Button(tab, text="Mock Google Calendar connect", command=self._mock_calendar_connect).pack(anchor=tk.W)
        ttk.Label(
            tab,
            text=(
                "Future versions: authenticate via OAuth 2.0, detect conflicts before scheduling, and tag events with "
                "Action Menu colors so analysis stays reliable."
            ),
            wraplength=800,
        ).pack(anchor=tk.W, pady=10)

        return tab

    # endregion build layout

    # region hydration
    def _hydrate_all(self) -> None:
        self._hydrate_reflections()
        self._refresh_goal_tree()
        self._refresh_habit_tree()
        self._refresh_weekly_lists()
        self._refresh_goal_dependent_controls()
        self._refresh_time_tree()
        self._refresh_flow_logs()
        self._refresh_quick_capture_tree()
        self._refresh_journal_history()

    def _hydrate_reflections(self) -> None:
        self.values_text.delete("1.0", tk.END)
        self.milestones_text.delete("1.0", tk.END)
        self.energy_text.delete("1.0", tk.END)
        self.values_text.insert(tk.END, self.state.reflections.values)
        self.milestones_text.insert(tk.END, self.state.reflections.milestones)
        self.energy_text.insert(tk.END, self.state.reflections.energy)

    def _refresh_goal_tree(self) -> None:
        self.goal_tree.delete(*self.goal_tree.get_children())
        for goal in self.state.goals:
            measure = goal.measurable or goal.time_bound
            self.goal_tree.insert(
                "",
                tk.END,
                iid=goal.id,
                values=(goal.title, goal.category, goal.horizon, measure),
            )

    def _refresh_habit_tree(self) -> None:
        self.habit_tree.delete(*self.habit_tree.get_children())
        for habit in self.state.habits:
            self.habit_tree.insert(
                "",
                tk.END,
                iid=habit.id,
                values=(habit.name, habit.frequency, habit.anchor, habit.linked_goal),
            )
        self.action_list.delete(0, tk.END)
        for habit in self.state.habits:
            label = f"{habit.name} → {habit.success_metric or 'track completion'}"
            self.action_list.insert(tk.END, label)

    def _refresh_weekly_lists(self) -> None:
        for bucket, listbox in self.week_lists.items():
            listbox.delete(0, tk.END)
            for action in self.state.weekly_actions.get(bucket, []):
                listbox.insert(tk.END, action)
        self.today_focus.delete(0, tk.END)
        for action in self.state.weekly_actions.get("Today", [])[:3]:
            self.today_focus.insert(tk.END, action)

    def _refresh_goal_dependent_controls(self) -> None:
        goal_titles = [goal.title for goal in self.state.goals]
        self.habit_goal.configure(values=goal_titles)
        motivation_options = goal_titles + [habit.name for habit in self.state.habits]
        self.action_motivation.configure(values=motivation_options)

    def _refresh_time_tree(self) -> None:
        self.time_tree.delete(*self.time_tree.get_children())
        for entry in self.state.time_entries:
            self.time_tree.insert(
                "",
                tk.END,
                iid=entry.id,
                values=(
                    entry.activity,
                    entry.category,
                    entry.start.strftime("%b %d %H:%M"),
                    f"{entry.duration_hours:.2f}",
                    entry.calendar_color,
                ),
            )
        self._refresh_effort_summary()

    def _refresh_flow_logs(self) -> None:
        self.flow_log_tree.delete(*self.flow_log_tree.get_children())
        for log in self.state.flow_logs:
            related = next((entry for entry in self.state.time_entries if entry.id == log.time_entry_id), None)
            activity = related.activity if related else "Session"
            self.flow_log_tree.insert(
                "",
                tk.END,
                values=(
                    activity,
                    log.flow_before,
                    log.flow_after,
                    log.emotion_after,
                    log.created_at.strftime("%b %d %H:%M"),
                ),
            )
        if not self.state.flow_logs:
            self.flow_summary.set("Flow data pending first log.")
            return
        avg_before = sum(log.flow_before for log in self.state.flow_logs) / len(self.state.flow_logs)
        avg_after = sum(log.flow_after for log in self.state.flow_logs) / len(self.state.flow_logs)
        self.flow_summary.set(
            f"Average flow {avg_before:.1f} → {avg_after:.1f}. Capture feelings to spot trends."
        )

    def _refresh_effort_summary(self) -> None:
        if not self.state.time_entries:
            self.effort_summary.set("No hours tracked yet.")
            return
        totals: Dict[str, float] = {}
        for entry in self.state.time_entries:
            totals[entry.category] = totals.get(entry.category, 0) + entry.duration_hours
        breakdown = ", ".join(f"{cat}: {hours:.2f}h" for cat, hours in totals.items())
        self.effort_summary.set(f"Effort invested → {breakdown}")

    def _refresh_quick_capture_tree(self) -> None:
        self.quick_tree.delete(*self.quick_tree.get_children())
        for item in self.state.quick_capture:
            self.quick_tree.insert(
                "",
                tk.END,
                iid=item.id,
                values=(item.text, item.status, item.created_at.strftime("%b %d %H:%M")),
            )

    def _refresh_journal_history(self) -> None:
        self.journal_history.delete(*self.journal_history.get_children())
        for entry in sorted(self.state.journal_entries, key=lambda e: e.created_at, reverse=True):
            excerpt = (entry.text[:60] + "…") if len(entry.text) > 60 else entry.text
            self.journal_history.insert(
                "",
                tk.END,
                iid=entry.id,
                values=(entry.created_at.strftime("%b %d %H:%M"), excerpt),
            )

    # endregion hydration

    # region actions
    def _commit_intentions(self) -> None:
        reflections = self.state.reflections
        reflections.values = self.values_text.get("1.0", tk.END).strip()
        reflections.milestones = self.milestones_text.get("1.0", tk.END).strip()
        reflections.energy = self.energy_text.get("1.0", tk.END).strip()
        self._persist()
        messagebox.showinfo("Intentions locked", "Great! These reflections fuel the rest of the menu.")

    def _add_goal(self) -> None:
        title = self.goal_vars["title"].get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Give the goal a clear title.")
            return
        category = self.goal_category.get() or "General"
        goal = SmartGoal.new(
            title=title,
            specific=self.goal_vars["specific"].get().strip(),
            measurable=self.goal_vars["measurable"].get().strip(),
            achievable=self.goal_vars["achievable"].get().strip(),
            relevant=self.goal_vars["relevant"].get().strip(),
            time_bound=self.goal_vars["time_bound"].get().strip(),
            horizon=self.goal_horizon.get(),
            category=category,
            calendar_color=CATEGORY_COLORS.get(category, "default"),
        )
        self.state.goals.append(goal)
        self._persist()
        self._refresh_goal_tree()
        self._refresh_goal_dependent_controls()
        for entry in self.goal_vars.values():
            entry.delete(0, tk.END)

    def _add_habit(self) -> None:
        name = self.habit_entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Missing habit", "Name the habit to remember it later.")
            return
        habit = HabitPlan.new(
            name=name,
            anchor=self.habit_entries["anchor"].get().strip(),
            frequency=self.habit_entries["frequency"].get().strip(),
            success_metric=self.habit_entries["success_metric"].get().strip(),
            linked_goal=self.habit_goal.get() or "",
        )
        self.state.habits.append(habit)
        self._persist()
        self._refresh_habit_tree()
        self._refresh_goal_dependent_controls()
        for entry in self.habit_entries.values():
            entry.delete(0, tk.END)

    def _add_weekly_action(self) -> None:
        action = self.action_entry.get().strip()
        if not action:
            messagebox.showwarning("Missing action", "Describe the move you want to make.")
            return
        bucket = self.action_timeframe.get()
        motivation = self.action_motivation.get()
        label = f"{action} ({motivation})" if motivation else action
        self.state.weekly_actions.setdefault(bucket, []).append(label)
        self._persist()
        self._refresh_weekly_lists()
        self.action_entry.delete(0, tk.END)

    def _send_focus_to_today(self) -> None:
        today_items = self.state.weekly_actions.get("Today", [])
        if not today_items:
            messagebox.showinfo("Action Menu", "Add at least one action to the Today bucket first.")
            return
        self.today_focus.delete(0, tk.END)
        for item in today_items[:3]:
            self.today_focus.insert(tk.END, item)

    def _start_timer(self) -> None:
        if self.timer_start is not None:
            messagebox.showinfo("Action Menu", "Timer already running. Stop it before starting a new block.")
            return
        activity = self.timer_activity.get().strip()
        if not activity:
            messagebox.showwarning("Need activity", "Describe the experiment or task before starting the timer.")
            return
        category = self.timer_category.get() or "Creative"
        self.timer_start = datetime.utcnow()
        self.pending_flow_context = {
            "activity": activity,
            "category": category,
            "flow_before": int(self.flow_before_var.get()),
            "emotion_before": self.emotion_before_var.get(),
        }
        self.timer_status.set(f"Timer running: {activity} ({category})")

    def _stop_timer(self) -> None:
        if self.timer_start is None:
            messagebox.showinfo("Action Menu", "Start the timer first.")
            return
        context = self.pending_flow_context or {
            "activity": self.timer_activity.get().strip() or "Deep work",
            "category": self.timer_category.get() or "Creative",
            "flow_before": int(self.flow_before_var.get()),
            "emotion_before": self.emotion_before_var.get(),
        }
        start = self.timer_start
        end = datetime.utcnow()
        self.timer_start = None
        self.pending_flow_context = None
        self.timer_status.set("Timer idle")
        self._record_time_entry(
            activity=context["activity"],
            category=context["category"],
            start=start,
            end=end,
            flow_context=context,
        )

    def _manual_time_entry(self) -> None:
        activity = self.timer_activity.get().strip()
        if not activity:
            messagebox.showwarning("Need activity", "Fill in the activity field before logging manually.")
            return
        category = self.timer_category.get() or "Creative"
        duration = simpledialog.askfloat(
            "Manual log",
            "How many hours should we log?",
            minvalue=0.1,
            maxvalue=12.0,
            initialvalue=0.5,
        )
        if duration is None:
            return
        end = datetime.utcnow()
        start = end - timedelta(hours=duration)
        context = {
            "activity": activity,
            "category": category,
            "flow_before": int(self.flow_before_var.get()),
            "emotion_before": self.emotion_before_var.get(),
        }
        self._record_time_entry(activity=activity, category=category, start=start, end=end, flow_context=context)

    def _record_time_entry(
        self,
        *,
        activity: str,
        category: str,
        start: datetime,
        end: datetime,
        flow_context: Dict[str, int | str] | None,
    ) -> None:
        entry = TimeEntry.new(
            activity=activity,
            category=category,
            start=start,
            end=end,
            calendar_color=CATEGORY_COLORS.get(category, "default"),
        )
        self.state.time_entries.append(entry)
        self._persist()
        self._refresh_time_tree()
        self._launch_flow_capture(entry, flow_context)

    def _launch_flow_capture(self, entry: TimeEntry, flow_context: Dict[str, int | str] | None) -> None:
        if not flow_context:
            return
        dialog = FlowCaptureDialog(
            self,
            activity=entry.activity,
            flow_before=int(flow_context.get("flow_before", 3)),
            emotion_before=str(flow_context.get("emotion_before", EMOTIONS[0])),
        )
        self.wait_window(dialog)
        if dialog.result:
            self._store_flow_log(entry, flow_context, dialog.result)

    def _store_flow_log(
        self,
        entry: TimeEntry,
        flow_context: Dict[str, int | str],
        result: Dict[str, int | str],
    ) -> None:
        log = FlowLog.new(
            time_entry_id=entry.id,
            flow_before=int(flow_context.get("flow_before", 3)),
            flow_after=int(result["flow_after"]),
            emotion_before=str(flow_context.get("emotion_before", "")),
            emotion_after=str(result["emotion_after"]),
            feeling_message=str(result["message"]),
            feeling_motivation=str(result["motivation"]),
        )
        self.state.flow_logs.append(log)
        self._persist()
        self._refresh_flow_logs()

    def _save_journal_entry(self) -> None:
        text = self.journal_text.get("1.0", tk.END).strip()
        if not text:
            messagebox.showwarning("Journal", "Write something before saving.")
            return
        suggestions = extract_suggestions(text)
        tags = self._infer_tags(text)
        entry = JournalEntry.new(text=text, tags=tags, suggestions=suggestions)
        self.state.journal_entries.append(entry)
        self._persist()
        self._refresh_journal_history()
        self._display_suggestions(suggestions)
        self._set_journal_detail(entry.text)
        self.journal_text.delete("1.0", tk.END)
        messagebox.showinfo("Journal", f"Entry saved with {len(suggestions)} suggestion(s).")

    def _update_journal_suggestions(self) -> None:
        text = self.journal_text.get("1.0", tk.END).strip()
        if not text:
            self.current_suggestions = []
            self.journal_suggestions.delete(0, tk.END)
            self.journal_suggestions.insert(tk.END, "Keep writing for insights…")
            return
        suggestions = extract_suggestions(text)
        self._display_suggestions(suggestions)
        if not suggestions:
            self.journal_suggestions.insert(tk.END, "No actionable phrases yet – keep riffing.")

    def _display_suggestions(self, suggestions: List[JournalSuggestion]) -> None:
        self.current_suggestions = suggestions
        self.journal_suggestions.delete(0, tk.END)
        for suggestion in suggestions:
            label = f"[{suggestion.kind}] {suggestion.text}"
            self.journal_suggestions.insert(tk.END, label)

    def _set_journal_detail(self, text: str) -> None:
        self.journal_detail.configure(state=tk.NORMAL)
        self.journal_detail.delete("1.0", tk.END)
        self.journal_detail.insert(tk.END, text)
        self.journal_detail.configure(state=tk.DISABLED)

    def _infer_tags(self, text: str) -> List[str]:
        lowered = text.lower()
        tags = [category for category in CATEGORY_OPTIONS if category.lower() in lowered]
        if "rest" in lowered or "recover" in lowered:
            tags.append("Recovery")
        return sorted(set(tags))

    def _get_selected_suggestion(self) -> JournalSuggestion | None:
        selection = self.journal_suggestions.curselection()
        if not selection:
            messagebox.showinfo("Journal", "Select a suggestion first.")
            return None
        index = selection[0]
        if index >= len(self.current_suggestions):
            return None
        return self.current_suggestions[index]

    def _suggestion_to_today(self) -> None:
        suggestion = self._get_selected_suggestion()
        if not suggestion:
            return
        bucket = self.state.weekly_actions.setdefault("Today", [])
        bucket.append(suggestion.text)
        self._persist()
        self._refresh_weekly_lists()
        messagebox.showinfo("Journal", "Added suggestion to Today focus.")

    def _suggestion_to_goal(self) -> None:
        suggestion = self._get_selected_suggestion()
        if not suggestion:
            return
        field = self.goal_vars.get("title")
        if field is None:
            return
        field.delete(0, tk.END)
        field.insert(0, suggestion.text)
        messagebox.showinfo("Journal", "Drafted the text into the goal title field.")

    def _suggestion_to_habit(self) -> None:
        suggestion = self._get_selected_suggestion()
        if not suggestion:
            return
        field = self.habit_entries.get("name")
        if field is None:
            return
        field.delete(0, tk.END)
        field.insert(0, suggestion.text)
        messagebox.showinfo("Journal", "Drafted the text into the habit name field.")

    def _suggestion_to_capture(self) -> None:
        suggestion = self._get_selected_suggestion()
        if not suggestion:
            return
        item = QuickCaptureItem.new(text=suggestion.text)
        self.state.quick_capture.append(item)
        self._persist()
        self._refresh_quick_capture_tree()
        messagebox.showinfo("Journal", "Captured suggestion into the Inbox.")

    def _on_journal_select(self, _event: tk.Event) -> None:
        selection = self.journal_history.selection()
        if not selection:
            return
        entry_id = selection[0]
        entry = next((item for item in self.state.journal_entries if item.id == entry_id), None)
        if not entry:
            return
        self._set_journal_detail(entry.text)
        self._display_suggestions(entry.suggestions)

    def _add_quick_item(self) -> None:
        text = self.quick_entry.get().strip()
        if not text:
            messagebox.showwarning("Quick capture", "Drop a thought before hitting capture.")
            return
        item = QuickCaptureItem.new(text=text)
        self.state.quick_capture.append(item)
        self.quick_entry.delete(0, tk.END)
        self._persist()
        self._refresh_quick_capture_tree()

    def _update_quick_status(self, status: str) -> None:
        if status not in QUICK_CAPTURE_STATUSES:
            return
        selection = self.quick_tree.selection()
        if not selection:
            messagebox.showinfo("Quick capture", "Select one or more items first.")
            return
        updated = 0
        for item_id in selection:
            item = next((entry for entry in self.state.quick_capture if entry.id == item_id), None)
            if item and item.status != status:
                item.status = status
                updated += 1
        if updated:
            self._persist()
            self._refresh_quick_capture_tree()
        self.quick_status_msg.set(f"{updated} item(s) → {status}")

    def _delete_quick_item(self) -> None:
        selection = self.quick_tree.selection()
        if not selection:
            messagebox.showinfo("Quick capture", "Select an item to delete.")
            return
        before = len(self.state.quick_capture)
        self.state.quick_capture = [item for item in self.state.quick_capture if item.id not in selection]
        removed = before - len(self.state.quick_capture)
        if removed:
            self._persist()
            self._refresh_quick_capture_tree()
        self.quick_status_msg.set(f"Removed {removed} item(s)")

    def _mock_calendar_connect(self) -> None:
        messagebox.showinfo(
            "Integrations",
            "Pretending to connect to Google Calendar. Future builds will detect conflicts and sync colors.",
        )

    def _persist(self) -> None:
        self.storage.save(self.state)


class FlowCaptureDialog(tk.Toplevel):
    def __init__(
        self,
        parent: tk.Widget,
        *,
        activity: str,
        flow_before: int,
        emotion_before: str,
    ) -> None:
        super().__init__(parent)
        self.result: Dict[str, int | str] | None = None
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
        default_emotion = emotion_before if emotion_before in EMOTIONS else EMOTIONS[0]
        self.emotion_var = tk.StringVar(value=default_emotion)
        ttk.Combobox(container, values=EMOTIONS, textvariable=self.emotion_var, state="readonly").pack(fill=tk.X)

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


if __name__ == "__main__":
    app = ActionMenuApp()
    app.mainloop()
