"""Action Menu prototype built with Tkinter.

The application helps users translate long-term aspirations into SMART goals,
habits, weekly plans, and tracked effort. It is intentionally self-contained so it
can serve as a desktop prototype before a potential web version.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List
import tkinter as tk
from tkinter import messagebox, ttk


@dataclass
class SmartGoal:
    title: str
    specific: str
    measurable: str
    achievable: str
    relevant: str
    time_bound: str
    horizon: str  # today / this week / this month / long term


@dataclass
class HabitPlan:
    name: str
    anchor: str
    frequency: str
    success_metric: str
    linked_goal: str


@dataclass
class TimeEntry:
    activity: str
    category: str
    start: datetime
    end: datetime

    @property
    def duration_hours(self) -> float:
        return round((self.end - self.start).total_seconds() / 3600, 2)


class ActionMenuApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Action Menu")
        self.geometry("1200x780")
        self.minsize(1000, 720)

        self.goals: List[SmartGoal] = []
        self.habits: List[HabitPlan] = []
        self.weekly_actions: Dict[str, List[str]] = {"Today": [], "This Week": [], "This Month": []}
        self.time_entries: List[TimeEntry] = []
        self.current_timer: TimeEntry | None = None
        self.timer_start: datetime | None = None

        self._build_style()
        self._build_layout()

    def _build_style(self) -> None:
        style = ttk.Style(self)
        style.configure("Header.TLabel", font=("Segoe UI", 20, "bold"))
        style.configure("Subheader.TLabel", font=("Segoe UI", 12))
        style.configure("Card.TLabelframe", padding=12)
        style.configure("Card.TLabelframe.Label", font=("Segoe UI", 12, "bold"))

    def _build_layout(self) -> None:
        header = ttk.Frame(self, padding=20)
        header.pack(fill=tk.X)
        ttk.Label(header, text="Action Menu", style="Header.TLabel").pack(anchor=tk.W)
        ttk.Label(
            header,
            text=(
                "Design your week around what matters: clarify values, craft SMART goals, "
                "install habits, plan actions, and track the hours that move the needle."
            ),
            style="Subheader.TLabel",
            wraplength=900,
            justify=tk.LEFT,
        ).pack(anchor=tk.W, pady=(6, 0))

        notebook = ttk.Notebook(self)
        notebook.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))

        notebook.add(self._build_vision_tab(notebook), text="North Star")
        notebook.add(self._build_goals_tab(notebook), text="SMART Goals")
        notebook.add(self._build_habits_tab(notebook), text="Habits & Actions")
        notebook.add(self._build_weekly_tab(notebook), text="Weekly Menu")
        notebook.add(self._build_time_tab(notebook), text="Time Tracker")
        notebook.add(self._build_integrations_tab(notebook), text="Integrations")

    def _build_vision_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        prompts = (
            "Why do I care about these ambitions?",
            "What would a wildly successful week look like?",
            "What experiments prove I'm living authentically?",
        )
        ttk.Label(tab, text="Authentic Life Prompts", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
        prompt_box = tk.Text(tab, height=6, wrap=tk.WORD)
        prompt_box.insert(tk.END, "\n".join(f"• {p}" for p in prompts))
        prompt_box.configure(state=tk.DISABLED, bg="#f8f8f8", relief=tk.FLAT)
        prompt_box.pack(fill=tk.X, pady=(6, 12))

        input_frame = ttk.Frame(tab)
        input_frame.pack(fill=tk.BOTH, expand=True)

        self.values_text = self._add_labeled_text(input_frame, "Values & Why it matters", 0)
        self.milestones_text = self._add_labeled_text(input_frame, "Milestones for next 12 months", 1)
        self.energy_text = self._add_labeled_text(input_frame, "Energy / Recovery rituals", 2)

        ttk.Button(tab, text="Commit Intentions", command=self._commit_intentions).pack(anchor=tk.E, pady=10)
        return tab

    def _add_labeled_text(self, parent: ttk.Frame, label: str, column: int, *, height: int = 8) -> tk.Text:
        frame = ttk.Labelframe(parent, text=label, style="Card.TLabelframe")
        frame.grid(row=0, column=column, sticky="nsew", padx=6)
        parent.columnconfigure(column, weight=1)
        text_widget = tk.Text(frame, height=height, wrap=tk.WORD)
        text_widget.pack(fill=tk.BOTH, expand=True)
        return text_widget

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

        ttk.Label(form, text="Horizon (today, week, month, long term)").grid(row=len(fields), column=0, sticky=tk.W, pady=3)
        self.goal_horizon = ttk.Combobox(form, values=["Today", "This Week", "This Month", "Long Term"], state="readonly")
        self.goal_horizon.current(3)
        self.goal_horizon.grid(row=len(fields), column=1, sticky=tk.EW, padx=6, pady=3)

        ttk.Button(form, text="Add goal", command=self._add_goal).grid(row=len(fields) + 1, column=1, sticky=tk.E, pady=8)

        self.goal_tree = ttk.Treeview(
            tab,
            columns=("title", "horizon", "measure"),
            show="headings",
            height=10,
        )
        self.goal_tree.heading("title", text="Goal")
        self.goal_tree.heading("horizon", text="Horizon")
        self.goal_tree.heading("measure", text="Key Metric")
        self.goal_tree.column("title", width=300)
        self.goal_tree.column("horizon", width=100, anchor=tk.CENTER)
        self.goal_tree.column("measure", width=200)
        self.goal_tree.pack(fill=tk.BOTH, expand=True, pady=12)

        return tab

    def _build_habits_tab(self, parent: ttk.Notebook) -> ttk.Frame:
        tab = ttk.Frame(parent, padding=20)

        form = ttk.Labelframe(tab, text="Habit design using cue-action-celebrate", style="Card.TLabelframe")
        form.pack(fill=tk.X)

        self.habit_entries: Dict[str, ttk.Entry] = {}
        fields = [
            ("Habit name", "name"),
            ("Anchor / trigger", "anchor"),
            ("Frequency (daily, 3x week, etc.)", "frequency"),
            ("Success metric", "success_metric"),
        ]
        for idx, (label, key) in enumerate(fields):
            ttk.Label(form, text=label).grid(row=idx, column=0, sticky=tk.W, pady=3)
            entry = ttk.Entry(form)
            entry.grid(row=idx, column=1, sticky=tk.EW, padx=6, pady=3)
            self.habit_entries[key] = entry
        form.columnconfigure(1, weight=1)

        ttk.Label(form, text="Linked goal (optional)").grid(row=len(fields), column=0, sticky=tk.W, pady=3)
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

        ttk.Label(tab, text="Micro-actions that prove momentum:").pack(anchor=tk.W)
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
        self.action_timeframe = ttk.Combobox(form, values=list(self.weekly_actions.keys()), state="readonly")
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
        for idx, bucket in enumerate(self.weekly_actions):
            frame = ttk.Labelframe(board, text=bucket, padding=6)
            frame.grid(row=0, column=idx, sticky="nsew", padx=6)
            listbox = tk.Listbox(frame, height=12)
            listbox.pack(fill=tk.BOTH, expand=True)
            self.week_lists[bucket] = listbox

        ttk.Label(tab, text="Ritual: choose 3 focus moves for today.").pack(anchor=tk.W, pady=(6, 0))
        self.today_focus = tk.Listbox(tab, height=4)
        self.today_focus.pack(fill=tk.X, pady=6)

        ttk.Button(tab, text="Send focus to Today list", command=self._send_focus_to_today).pack(anchor=tk.E)

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
            values=[
                "Creative", "Learning", "Shipping", "Body", "Recovery",
            ],
            state="readonly",
        )
        self.timer_category.current(0)
        self.timer_category.grid(row=1, column=1, sticky=tk.EW, padx=6, pady=3)

        button_frame = ttk.Frame(form)
        button_frame.grid(row=2, column=0, columnspan=2, pady=6)
        ttk.Button(button_frame, text="Start", command=self._start_timer).grid(row=0, column=0, padx=6)
        ttk.Button(button_frame, text="Stop & log", command=self._stop_timer).grid(row=0, column=1, padx=6)
        ttk.Button(button_frame, text="Manual log", command=self._manual_time_entry).grid(row=0, column=2, padx=6)

        self.timer_status = tk.StringVar(value="Timer idle")
        ttk.Label(tab, textvariable=self.timer_status, foreground="#0078d4").pack(anchor=tk.W, pady=(10, 0))

        self.time_tree = ttk.Treeview(tab, columns=("activity", "category", "start", "duration"), show="headings", height=10)
        for col, label in zip(("activity", "category", "start", "duration"), ("Activity", "Category", "Start", "Hours")):
            self.time_tree.heading(col, text=label)
            anchor = tk.CENTER if col in {"category", "duration"} else tk.W
            self.time_tree.column(col, anchor=anchor, width=120 if col != "activity" else 260)
        self.time_tree.pack(fill=tk.BOTH, expand=True, pady=12)

        self.effort_summary = tk.StringVar(value="No hours tracked yet.")
        ttk.Label(tab, textvariable=self.effort_summary, wraplength=900).pack(anchor=tk.W)

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

        # Prototype Google Calendar connection
        ttk.Button(tab, text="Mock Google Calendar connect", command=self._mock_calendar_connect).pack(anchor=tk.W)
        ttk.Label(
            tab,
            text="Later versions can use Google Calendar API (OAuth + calendar.events.insert) for real sync.",
            wraplength=800,
        ).pack(anchor=tk.W, pady=10)

        return tab

    def _commit_intentions(self) -> None:
        values = self.values_text.get("1.0", tk.END).strip()
        milestones = self.milestones_text.get("1.0", tk.END).strip()
        energy = self.energy_text.get("1.0", tk.END).strip()
        if not (values or milestones or energy):
            messagebox.showinfo("Action Menu", "Write at least one reflection before committing.")
            return
        messagebox.showinfo(
            "Intentions locked",
            "Great! These reflections fuel the rest of the menu. Revisit them weekly.",
        )

    def _add_goal(self) -> None:
        title = self.goal_vars["title"].get().strip()
        if not title:
            messagebox.showwarning("Missing title", "Give the goal a clear title.")
            return
        goal = SmartGoal(
            title=title,
            specific=self.goal_vars["specific"].get().strip(),
            measurable=self.goal_vars["measurable"].get().strip(),
            achievable=self.goal_vars["achievable"].get().strip(),
            relevant=self.goal_vars["relevant"].get().strip(),
            time_bound=self.goal_vars["time_bound"].get().strip(),
            horizon=self.goal_horizon.get(),
        )
        self.goals.append(goal)
        self.goal_tree.insert("", tk.END, values=(goal.title, goal.horizon, goal.measurable or goal.time_bound))
        self._refresh_goal_dependent_controls()
        for entry in self.goal_vars.values():
            entry.delete(0, tk.END)

    def _add_habit(self) -> None:
        name = self.habit_entries["name"].get().strip()
        if not name:
            messagebox.showwarning("Missing habit", "Name the habit to remember it later.")
            return
        habit = HabitPlan(
            name=name,
            anchor=self.habit_entries["anchor"].get().strip(),
            frequency=self.habit_entries["frequency"].get().strip(),
            success_metric=self.habit_entries["success_metric"].get().strip(),
            linked_goal=self.habit_goal.get() or "",
        )
        self.habits.append(habit)
        self.habit_tree.insert("", tk.END, values=(habit.name, habit.frequency, habit.anchor, habit.linked_goal))
        self.action_list.insert(tk.END, f"{habit.name} → {habit.success_metric or 'track completion'}")
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
        self.weekly_actions[bucket].append(label)
        self.week_lists[bucket].insert(tk.END, label)
        self.action_entry.delete(0, tk.END)

    def _send_focus_to_today(self) -> None:
        today_items = self.weekly_actions["Today"]
        if not today_items:
            messagebox.showinfo("Action Menu", "Add at least one action to the Today bucket first.")
            return
        self.today_focus.delete(0, tk.END)
        for item in today_items[:3]:
            self.today_focus.insert(tk.END, item)

    def _start_timer(self) -> None:
        if self.timer_start is not None:
            messagebox.showinfo("Timer running", "Stop the current block before starting a new one.")
            return
        activity = self.timer_activity.get().strip()
        if not activity:
            messagebox.showwarning("Missing activity", "Describe the deep-work block.")
            return
        self.timer_start = datetime.now()
        self.timer_status.set(f"Tracking: {activity}")

    def _stop_timer(self) -> None:
        if self.timer_start is None:
            messagebox.showinfo("Action Menu", "Start the timer to log focused hours.")
            return
        activity = self.timer_activity.get().strip()
        category = self.timer_category.get()
        end_time = datetime.now()
        entry = TimeEntry(
            activity=activity or "Untitled session",
            category=category,
            start=self.timer_start,
            end=end_time,
        )
        self.time_entries.append(entry)
        self.time_tree.insert(
            "",
            tk.END,
            values=(
                entry.activity,
                entry.category,
                entry.start.strftime("%b %d %H:%M"),
                f"{entry.duration_hours:.2f}",
            ),
        )
        self.timer_start = None
        self.timer_status.set("Timer idle")
        self.timer_activity.delete(0, tk.END)
        self._refresh_effort_summary()

    def _manual_time_entry(self) -> None:
        description = self.timer_activity.get().strip() or "Manual entry"
        category = self.timer_category.get()
        entry = TimeEntry(
            activity=description,
            category=category,
            start=datetime.now(),
            end=datetime.now(),
        )
        self.time_entries.append(entry)
        self.time_tree.insert(
            "",
            tk.END,
            values=(entry.activity, entry.category, entry.start.strftime("%b %d %H:%M"), "0.00"),
        )
        self._refresh_effort_summary()

    def _refresh_goal_dependent_controls(self) -> None:
        goal_titles = [goal.title for goal in self.goals]
        self.habit_goal.configure(values=goal_titles)
        current = self.habit_goal.get()
        if current not in goal_titles:
            self.habit_goal.set("")
        motivation_options = goal_titles + [habit.name for habit in self.habits]
        if not motivation_options:
            motivation_options = []
        self.action_motivation.configure(values=motivation_options)

    def _refresh_effort_summary(self) -> None:
        if not self.time_entries:
            self.effort_summary.set("No hours tracked yet.")
            return
        totals: Dict[str, float] = {}
        for entry in self.time_entries:
            totals[entry.category] = totals.get(entry.category, 0) + entry.duration_hours
        breakdown = ", ".join(f"{cat}: {hours:.2f}h" for cat, hours in totals.items())
        self.effort_summary.set(f"Effort invested → {breakdown}")

    def _mock_calendar_connect(self) -> None:
        messagebox.showinfo(
            "Google Calendar prototype",
            "Future version: authenticate via OAuth 2.0, then push weekly focus blocks into Calendar.",
        )


def main() -> None:
    app = ActionMenuApp()
    app.mainloop()


if __name__ == "__main__":
    main()
