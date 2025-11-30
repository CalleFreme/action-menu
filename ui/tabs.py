"""Notebook tab builders for Action Menu."""
from __future__ import annotations

from typing import TYPE_CHECKING, Dict
import tkinter as tk
from tkinter import ttk

from ui.constants import (
    ACTION_SAMPLE,
    CATEGORY_OPTIONS,
    EMOTIONS,
    GOAL_FIELD_SAMPLES,
    HABIT_FIELD_SAMPLES,
    QUICK_ENTRY_SAMPLE,
    TIMER_ACTIVITY_SAMPLE,
)

if TYPE_CHECKING:  # pragma: no cover
    from action_menu import ActionMenuApp


def _add_labeled_text(parent: ttk.Frame, label: str, column: int, *, height: int = 8) -> tk.Text:
    frame = ttk.Labelframe(parent, text=label, style="Card.TLabelframe")
    frame.grid(row=0, column=column, sticky="nsew", padx=6)
    parent.columnconfigure(column, weight=1)
    widget = tk.Text(frame, height=height, wrap=tk.WORD)
    widget.pack(fill=tk.BOTH, expand=True)
    return widget


def build_vision_tab(app: "ActionMenuApp", parent: ttk.Notebook) -> ttk.Frame:
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

    app.values_text = _add_labeled_text(input_frame, "Values & Why it matters", 0)
    app.milestones_text = _add_labeled_text(input_frame, "Milestones for next 12 months", 1)
    app.energy_text = _add_labeled_text(input_frame, "Energy / Recovery rituals", 2)

    ttk.Button(
        tab,
        text="Commit Intentions",
        command=app._commit_intentions,
        style="Accent.TButton",
    ).pack(anchor=tk.E, pady=10)
    return tab


def build_goals_tab(app: "ActionMenuApp", parent: ttk.Notebook) -> ttk.Frame:
    tab = ttk.Frame(parent, padding=20)

    ttk.Label(
        tab,
        text="Clarify one SMART goal at a time—start with the next milestone that unblocks everything else.",
        wraplength=900,
    ).pack(anchor=tk.W, pady=(0, 8))

    form = ttk.Labelframe(tab, text="Define a SMART goal", style="Card.TLabelframe")
    form.pack(fill=tk.X)

    app.goal_vars = {}
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
        app.goal_vars[key] = entry
        sample = GOAL_FIELD_SAMPLES.get(key)
        if sample:
            entry.insert(0, sample)
        app._bind_submit(entry, app._add_goal)
    form.columnconfigure(1, weight=1)

    ttk.Label(form, text="Horizon").grid(row=len(fields), column=0, sticky=tk.W, pady=3)
    app.goal_horizon = ttk.Combobox(form, values=["Today", "This Week", "This Month", "Long Term"], state="readonly")
    app.goal_horizon.current(3)
    app.goal_horizon.grid(row=len(fields), column=1, sticky=tk.EW, padx=6, pady=3)

    ttk.Label(form, text="Category").grid(row=len(fields) + 1, column=0, sticky=tk.W, pady=3)
    app.goal_category = ttk.Combobox(form, values=CATEGORY_OPTIONS, state="readonly")
    app.goal_category.current(0)
    app.goal_category.grid(row=len(fields) + 1, column=1, sticky=tk.EW, padx=6, pady=3)

    ttk.Button(form, text="Add goal", command=app._add_goal).grid(row=len(fields) + 2, column=1, sticky=tk.E, pady=8)

    app.goal_tree = ttk.Treeview(
        tab,
        columns=("title", "category", "horizon", "measure"),
        show="headings",
        height=10,
    )
    for col, label in zip(
        ("title", "category", "horizon", "measure"),
        ("Goal", "Category", "Horizon", "Key Metric"),
    ):
        app.goal_tree.heading(col, text=label)
        anchor = tk.CENTER if col in {"category", "horizon"} else tk.W
        width = 120 if col != "title" else 320
        app.goal_tree.column(col, anchor=anchor, width=width)
    app.goal_tree.pack(fill=tk.BOTH, expand=True, pady=12)
    app._attach_tooltip(
        app.goal_tree,
        "Store each goal with category + horizon. Use the buttons above to add new entries and double-click to review details.",
    )

    return tab


def build_habits_tab(app: "ActionMenuApp", parent: ttk.Notebook) -> ttk.Frame:
    tab = ttk.Frame(parent, padding=20)

    ttk.Label(
        tab,
        text="Design habits by pairing a simple cue with a tiny celebration—keep the loop obvious and rewarding.",
        wraplength=900,
    ).pack(anchor=tk.W, pady=(0, 8))

    form = ttk.Labelframe(tab, text="Habit design (cue → action → celebrate)", style="Card.TLabelframe")
    form.pack(fill=tk.X)

    app.habit_entries = {}
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
        app.habit_entries[key] = entry
        sample = HABIT_FIELD_SAMPLES.get(key)
        if sample:
            entry.insert(0, sample)
        app._bind_submit(entry, app._add_habit)
    form.columnconfigure(1, weight=1)

    ttk.Label(form, text="Linked goal").grid(row=len(fields), column=0, sticky=tk.W, pady=3)
    app.habit_goal = ttk.Combobox(form, values=[], state="readonly")
    app.habit_goal.grid(row=len(fields), column=1, sticky=tk.EW, padx=6, pady=3)

    ttk.Button(form, text="Add habit", command=app._add_habit).grid(row=len(fields) + 1, column=1, sticky=tk.E, pady=8)

    app.habit_tree = ttk.Treeview(
        tab,
        columns=("name", "frequency", "anchor", "goal"),
        show="headings",
        height=9,
    )
    for col, label in zip(("name", "frequency", "anchor", "goal"), ("Habit", "Frequency", "Anchor", "Goal")):
        app.habit_tree.heading(col, text=label)
        app.habit_tree.column(col, anchor=tk.W, width=150)
    app.habit_tree.pack(fill=tk.BOTH, expand=True, pady=12)
    app._attach_tooltip(
        app.habit_tree,
        "Habits pull from the cue/anchor you define above. Link them to goals for better context.",
    )

    ttk.Label(tab, text="Micro-actions spawned by habits:").pack(anchor=tk.W)
    app.action_list = tk.Listbox(tab, height=5)
    app.action_list.pack(fill=tk.X, pady=(6, 0))
    app._attach_tooltip(
        app.action_list,
        "Use this list as inspiration for quick actions pulled from your habits.",
    )

    return tab


def build_weekly_tab(app: "ActionMenuApp", parent: ttk.Notebook) -> ttk.Frame:
    tab = ttk.Frame(parent, padding=20)

    ttk.Label(
        tab,
        text="Send your favorite experiments into the Weekly Menu, then promote just a few into Today focus.",
        wraplength=900,
    ).pack(anchor=tk.W, pady=(0, 8))

    form = ttk.Labelframe(tab, text="Weekly action generator", style="Card.TLabelframe")
    form.pack(fill=tk.X)

    ttk.Label(form, text="Action description").grid(row=0, column=0, sticky=tk.W, pady=3)
    app.action_entry = ttk.Entry(form)
    app.action_entry.grid(row=0, column=1, sticky=tk.EW, padx=6, pady=3)
    app.action_entry.insert(0, ACTION_SAMPLE)
    app.action_entry.select_range(0, tk.END)
    app._bind_submit(app.action_entry, app._add_weekly_action)
    form.columnconfigure(1, weight=1)

    ttk.Label(form, text="Timeframe").grid(row=1, column=0, sticky=tk.W, pady=3)
    app.action_timeframe = ttk.Combobox(form, values=list(app.state.weekly_actions.keys()), state="readonly")
    app.action_timeframe.current(0)
    app.action_timeframe.grid(row=1, column=1, sticky=tk.EW, padx=6, pady=3)

    ttk.Label(form, text="Motivation (goal / habit)").grid(row=2, column=0, sticky=tk.W, pady=3)
    app.action_motivation = ttk.Combobox(form, state="readonly")
    app.action_motivation.grid(row=2, column=1, sticky=tk.EW, padx=6, pady=3)

    ttk.Button(form, text="Add to weekly menu", command=app._add_weekly_action).grid(row=3, column=1, sticky=tk.E, pady=8)

    board = ttk.Frame(tab)
    board.pack(fill=tk.BOTH, expand=True, pady=12)
    board.columnconfigure((0, 1, 2), weight=1)

    app.week_lists = {}
    for idx, bucket in enumerate(app.state.weekly_actions):
        frame = ttk.Labelframe(board, text=bucket, padding=6)
        frame.grid(row=0, column=idx, sticky="nsew", padx=6)
        listbox = tk.Listbox(frame, height=12)
        listbox.pack(fill=tk.BOTH, expand=True)
        app.week_lists[bucket] = listbox
        app._attach_tooltip(
            listbox,
            "Drop actions into this bucket. Drag-and-drop isn't enabled yet, so use the form above to add items.",
        )

    ttk.Label(tab, text="Today Focus (pick three)").pack(anchor=tk.W, pady=(6, 0))
    app.today_focus = tk.Listbox(tab, height=4)
    app.today_focus.pack(fill=tk.X, pady=6)
    app._attach_tooltip(
        app.today_focus,
        "Limit Today to three high-leverage moves—this keeps the day realistic.",
    )

    ttk.Button(tab, text="Send top items to Today", command=app._send_focus_to_today).pack(anchor=tk.E)

    return tab


def build_time_tab(app: "ActionMenuApp", parent: ttk.Notebook) -> ttk.Frame:
    tab = ttk.Frame(parent, padding=20)

    ttk.Label(
        tab,
        text="Track deep work blocks and capture how you felt before/after to spot energy patterns.",
        wraplength=900,
    ).pack(anchor=tk.W, pady=(0, 8))

    form = ttk.Labelframe(tab, text="Deep work timer", style="Card.TLabelframe")
    form.pack(fill=tk.X)

    ttk.Label(form, text="Activity / experiment").grid(row=0, column=0, sticky=tk.W, pady=3)
    app.timer_activity = ttk.Entry(form)
    app.timer_activity.grid(row=0, column=1, sticky=tk.EW, padx=6, pady=3)
    app.timer_activity.insert(0, TIMER_ACTIVITY_SAMPLE)
    app.timer_activity.select_range(0, tk.END)
    form.columnconfigure(1, weight=1)

    ttk.Label(form, text="Category").grid(row=1, column=0, sticky=tk.W, pady=3)
    app.timer_category = ttk.Combobox(
        form,
        values=app.state.timer_categories,
        state="readonly",
    )
    app.timer_category.current(0)
    app.timer_category.grid(row=1, column=1, sticky=tk.EW, padx=6, pady=3)

    mood_frame = ttk.Frame(form)
    mood_frame.grid(row=2, column=0, columnspan=2, sticky=tk.EW, pady=6)
    ttk.Label(mood_frame, text="Flow before block (1-5)").grid(row=0, column=0, sticky=tk.W)
    app.flow_before_var = tk.IntVar(value=3)
    flow_scale = ttk.Scale(mood_frame, from_=1, to=5, orient=tk.HORIZONTAL, variable=app.flow_before_var)
    flow_scale.grid(row=0, column=1, sticky=tk.EW, padx=6)
    app._attach_tooltip(flow_scale, "How ready or focused do you feel right now? 1 = scattered, 5 = peak flow.")
    mood_frame.columnconfigure(1, weight=1)
    ttk.Label(mood_frame, text="Emotion right now").grid(row=1, column=0, sticky=tk.W, pady=3)
    app.emotion_before_var = tk.StringVar(value=EMOTIONS[0])
    emotion_combo = ttk.Combobox(mood_frame, values=EMOTIONS, textvariable=app.emotion_before_var, state="readonly")
    emotion_combo.grid(row=1, column=1, sticky=tk.EW, padx=6)
    app._attach_tooltip(emotion_combo, "Capture a quick emotion snapshot so you can correlate feelings with work types.")

    button_frame = ttk.Frame(form)
    button_frame.grid(row=3, column=0, columnspan=2, pady=6)
    ttk.Button(button_frame, text="Start", command=app._start_timer).grid(row=0, column=0, padx=6)
    ttk.Button(button_frame, text="Stop & log", command=app._stop_timer).grid(row=0, column=1, padx=6)
    ttk.Button(button_frame, text="Manual log", command=app._manual_time_entry).grid(row=0, column=2, padx=6)

    app.timer_status = tk.StringVar(value="Timer idle")
    status_label = ttk.Label(tab, textvariable=app.timer_status, foreground="#0078d4")
    status_label.pack(anchor=tk.W, pady=(10, 0))
    app._attach_tooltip(status_label, "Displays whether a block is actively running or logged.")

    app.time_tree = ttk.Treeview(
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
        app.time_tree.heading(col, text=label)
        app.time_tree.column(col, anchor=anchor, width=width)
    app.time_tree.pack(fill=tk.BOTH, expand=True, pady=12)
    app._attach_tooltip(
        app.time_tree,
        "Each entry includes color tags that align with categories—perfect for calendar exports later.",
    )

    app.effort_summary = tk.StringVar(value="No hours tracked yet.")
    ttk.Label(tab, textvariable=app.effort_summary, wraplength=900).pack(anchor=tk.W)

    app.flow_summary = tk.StringVar(value="Flow data pending first log.")
    ttk.Label(tab, textvariable=app.flow_summary, wraplength=900).pack(anchor=tk.W, pady=(4, 0))

    app.flow_log_tree = ttk.Treeview(
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
        app.flow_log_tree.heading(col, text=label)
        app.flow_log_tree.column(col, anchor=anchor, width=width)
    app.flow_log_tree.pack(fill=tk.BOTH, expand=True, pady=(6, 0))
    app._attach_tooltip(
        app.flow_log_tree,
        "Logging after-action flow + emotion reveals what work gives energy. Fill it in after each block.",
    )

    custom_cat = ttk.Labelframe(tab, text="Custom deep-work categories", style="Card.TLabelframe")
    custom_cat.pack(fill=tk.X, pady=(8, 0))
    ttk.Label(custom_cat, text="Add a category that matches your work vocabulary").grid(row=0, column=0, columnspan=2, sticky=tk.W)
    ttk.Label(custom_cat, text="Name").grid(row=1, column=0, sticky=tk.W, pady=(6, 0))
    app.new_timer_category = ttk.Entry(custom_cat)
    app.new_timer_category.grid(row=1, column=1, sticky=tk.EW, padx=6, pady=(6, 0))
    custom_cat.columnconfigure(1, weight=1)
    ttk.Button(custom_cat, text="Add category", command=app._add_timer_category).grid(row=2, column=1, sticky=tk.E, pady=6)
    app._attach_tooltip(
        custom_cat,
        "Examples: 'Mentorship', 'Game Design', 'Research'. Once added, choose it in the timer dropdown.",
    )
    app._bind_submit(app.new_timer_category, app._add_timer_category)

    return tab


def build_journal_tab(app: "ActionMenuApp", parent: ttk.Notebook) -> ttk.Frame:
    tab = ttk.Frame(parent, padding=20)

    ttk.Label(
        tab,
        text="Free-write on the left; the right panel highlights sentences you can turn into actions immediately.",
        wraplength=900,
    ).pack(anchor=tk.W, pady=(0, 8))

    editor = ttk.Frame(tab)
    editor.pack(fill=tk.BOTH, expand=True)
    editor.columnconfigure(0, weight=2)
    editor.columnconfigure(1, weight=1)

    left = ttk.Frame(editor)
    left.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
    ttk.Label(left, text="Daily journal (What happened today, anyway?)").pack(anchor=tk.W)
    app.journal_text = tk.Text(left, height=12, wrap=tk.WORD)
    app.journal_text.pack(fill=tk.BOTH, expand=True, pady=6)
    app.journal_text.bind("<KeyRelease>", lambda _event: app._update_journal_suggestions())
    app._attach_tooltip(
        app.journal_text,
        "Write freely; keywords like 'want to' or 'today' trigger suggestions automatically.",
    )
    ttk.Button(left, text="Save entry", command=app._save_journal_entry, style="Accent.TButton").pack(anchor=tk.E)

    right = ttk.Frame(editor)
    right.grid(row=0, column=1, sticky="nsew")
    ttk.Label(right, text="Actionable suggestions").pack(anchor=tk.W)
    app.journal_suggestions = tk.Listbox(right, height=6)
    app.journal_suggestions.pack(fill=tk.X, pady=4)
    app._attach_tooltip(
        app.journal_suggestions,
        "Select a line and draft it into Today focus, a goal, a habit, or the quick capture inbox.",
    )

    btns = ttk.Frame(right)
    btns.pack(fill=tk.X, pady=(4, 10))
    ttk.Button(btns, text="Add to Today", command=app._suggestion_to_today).grid(row=0, column=0, padx=4)
    ttk.Button(btns, text="Draft goal", command=app._suggestion_to_goal).grid(row=0, column=1, padx=4)
    ttk.Button(btns, text="Draft habit", command=app._suggestion_to_habit).grid(row=0, column=2, padx=4)
    ttk.Button(btns, text="Quick capture", command=app._suggestion_to_capture).grid(row=0, column=3, padx=4)

    ttk.Label(right, text="Journal history").pack(anchor=tk.W)
    app.journal_history = ttk.Treeview(
        right,
        columns=("timestamp", "excerpt"),
        show="headings",
        height=8,
    )
    app.journal_history.heading("timestamp", text="Captured")
    app.journal_history.heading("excerpt", text="Excerpt")
    app.journal_history.column("timestamp", width=140, anchor=tk.CENTER)
    app.journal_history.column("excerpt", width=240, anchor=tk.W)
    app.journal_history.pack(fill=tk.BOTH, expand=True)
    app.journal_history.bind("<<TreeviewSelect>>", app._on_journal_select)
    app._attach_tooltip(
        app.journal_history,
        "Tap any row to reload that entry's text and suggestions.",
    )

    app.journal_detail = tk.Text(tab, height=6, wrap=tk.WORD)
    app.journal_detail.configure(state=tk.DISABLED)
    app.journal_detail.pack(fill=tk.X, pady=(10, 0))

    app._update_journal_suggestions()

    return tab


def build_quick_capture_tab(app: "ActionMenuApp", parent: ttk.Notebook) -> ttk.Frame:
    tab = ttk.Frame(parent, padding=20)

    ttk.Label(
        tab,
        text="Treat this like an inbox—capture the thought, then triage it into Today, Later, or Archive when ready.",
        wraplength=900,
    ).pack(anchor=tk.W, pady=(0, 8))

    entry_frame = ttk.Frame(tab)
    entry_frame.pack(fill=tk.X)
    ttk.Label(entry_frame, text="Drop a thought, task, or idea:").grid(row=0, column=0, sticky=tk.W)
    app.quick_entry = ttk.Entry(entry_frame)
    app.quick_entry.grid(row=0, column=1, sticky=tk.EW, padx=6)
    app.quick_entry.insert(0, QUICK_ENTRY_SAMPLE)
    app.quick_entry.select_range(0, tk.END)
    app._bind_submit(app.quick_entry, app._add_quick_item)
    entry_frame.columnconfigure(1, weight=1)
    ttk.Button(entry_frame, text="Capture", command=app._add_quick_item).grid(row=0, column=2)
    app._attach_tooltip(
        app.quick_entry,
        "Keep it short—brain dumps, errand reminders, or creative sparks all belong here.",
    )

    ttk.Label(tab, text="Inbox → Today → Later → Archived").pack(anchor=tk.W, pady=(10, 0))
    app.quick_tree = ttk.Treeview(
        tab,
        columns=("text", "status", "created"),
        show="headings",
        height=12,
    )
    app.quick_tree.heading("text", text="Item")
    app.quick_tree.heading("status", text="Status")
    app.quick_tree.heading("created", text="Captured")
    app.quick_tree.column("text", width=360, anchor=tk.W)
    app.quick_tree.column("status", width=100, anchor=tk.CENTER)
    app.quick_tree.column("created", width=140, anchor=tk.CENTER)
    app.quick_tree.pack(fill=tk.BOTH, expand=True, pady=8)
    app._attach_tooltip(
        app.quick_tree,
        "Select one or more entries, then use the buttons below to pin to Today, schedule Later, archive, edit, or delete.",
    )

    action_bar = ttk.Frame(tab)
    action_bar.pack(fill=tk.X)
    ttk.Button(action_bar, text="Pin to Today", command=lambda: app._update_quick_status("Today")).grid(row=0, column=0, padx=4)
    ttk.Button(action_bar, text="Schedule Later", command=lambda: app._update_quick_status("Later")).grid(row=0, column=1, padx=4)
    ttk.Button(action_bar, text="Archive", command=lambda: app._update_quick_status("Archived")).grid(row=0, column=2, padx=4)
    ttk.Button(action_bar, text="Edit", command=app._edit_quick_item).grid(row=0, column=3, padx=4)
    ttk.Button(action_bar, text="Delete", command=app._delete_quick_item).grid(row=0, column=4, padx=4)

    app.quick_status_msg = tk.StringVar(value="")
    ttk.Label(tab, textvariable=app.quick_status_msg, foreground="#0078d4").pack(anchor=tk.W)

    return tab


def build_integrations_tab(app: "ActionMenuApp", parent: ttk.Notebook) -> ttk.Frame:
    tab = ttk.Frame(parent, padding=20)

    ttk.Label(tab, text="Prototype integrations", font=("Segoe UI", 14, "bold")).pack(anchor=tk.W)
    info = (
        "Export weekly plan to Google Calendar",
        "Sync time blocks with wearable or health data",
        "Push habit reminders via email or mobile notifications",
    )
    ttk.Label(tab, text="\n".join(f"• {line}" for line in info)).pack(anchor=tk.W, pady=10)

    ttk.Button(tab, text="Mock Google Calendar connect", command=app._mock_calendar_connect).pack(anchor=tk.W)
    ttk.Label(
        tab,
        text=(
            "Future versions: authenticate via OAuth 2.0, detect conflicts before scheduling, and tag events with "
            "Action Menu colors so analysis stays reliable."
        ),
        wraplength=800,
    ).pack(anchor=tk.W, pady=10)

    return tab
