"""Tkinter-based Action Menu prototype with persistence and journaling."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Callable, Dict, List
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
from ui.flow_dialog import FlowCaptureDialog
from ui.tooltips import Tooltip
from ui.constants import (
    ACTION_SAMPLE,
    CATEGORY_COLORS,
    CATEGORY_OPTIONS,
    DEFAULT_TIMER_CATEGORIES,
    EMOTIONS,
    GOAL_FIELD_SAMPLES,
    HABIT_FIELD_SAMPLES,
    QUICK_ENTRY_SAMPLE,
    TIMER_ACTIVITY_SAMPLE,
)
from ui import tabs as tab_builders

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
        if not self.state.timer_categories:
            self.state.timer_categories = list(DEFAULT_TIMER_CATEGORIES)

        self.timer_start: datetime | None = None
        self.pending_flow_context: Dict[str, int | str] | None = None
        self.current_suggestions: List[JournalSuggestion] = []
        self.flow_dialog: tk.Toplevel | None = None
        self._tooltips: List[Tooltip] = []

        self._build_style()
        self._build_layout()
        self._hydrate_all()

    # region build layout
    def _bind_submit(self, widget: tk.Widget, handler: Callable[[], None]) -> None:
        def _on_return(event: tk.Event) -> str:
            handler()
            return "break"

        widget.bind("<Return>", _on_return)

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

        notebook.add(tab_builders.build_vision_tab(self, notebook), text="North Star")
        notebook.add(tab_builders.build_goals_tab(self, notebook), text="SMART Goals")
        notebook.add(tab_builders.build_habits_tab(self, notebook), text="Habits & Actions")
        notebook.add(tab_builders.build_weekly_tab(self, notebook), text="Weekly Menu")
        notebook.add(tab_builders.build_time_tab(self, notebook), text="Time & Flow")
        notebook.add(tab_builders.build_journal_tab(self, notebook), text="Journal")
        notebook.add(tab_builders.build_quick_capture_tab(self, notebook), text="Quick Capture")
        notebook.add(tab_builders.build_integrations_tab(self, notebook), text="Integrations")

    def _attach_tooltip(self, widget: tk.Widget, text: str) -> None:
        self._tooltips.append(Tooltip(widget, text))

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

    def _format_local(self, value: datetime) -> str:
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone().strftime("%b %d %H:%M")

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
        self._refresh_timer_category_choices()

    def _refresh_timer_category_choices(self) -> None:
        if not hasattr(self, "timer_category"):
            return
        self.timer_category.configure(values=self.state.timer_categories)
        if self.timer_category.get() not in self.state.timer_categories and self.state.timer_categories:
            self.timer_category.set(self.state.timer_categories[0])

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
                    self._format_local(entry.start),
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
                    self._format_local(log.created_at),
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
                values=(item.text, item.status, self._format_local(item.created_at)),
            )

    def _refresh_journal_history(self) -> None:
        self.journal_history.delete(*self.journal_history.get_children())
        for entry in sorted(self.state.journal_entries, key=lambda e: e.created_at, reverse=True):
            excerpt = (entry.text[:60] + "…") if len(entry.text) > 60 else entry.text
            self.journal_history.insert(
                "",
                tk.END,
                iid=entry.id,
                values=(self._format_local(entry.created_at), excerpt),
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

    def _add_timer_category(self) -> None:
        if not hasattr(self, "new_timer_category"):
            return
        label = self.new_timer_category.get().strip()
        if not label:
            messagebox.showwarning("Time & Flow", "Name the category before adding it.")
            return
        if label in self.state.timer_categories:
            messagebox.showinfo("Time & Flow", "That category already exists.")
            return
        self.state.timer_categories.append(label)
        self._persist()
        self._refresh_timer_category_choices()
        self.timer_category.set(label)
        self.new_timer_category.delete(0, tk.END)

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
            emotions=EMOTIONS,
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

    def _edit_quick_item(self) -> None:
        selection = self.quick_tree.selection()
        if not selection:
            messagebox.showinfo("Quick capture", "Select an item to edit.")
            return
        item_id = selection[0]
        item = next((entry for entry in self.state.quick_capture if entry.id == item_id), None)
        if not item:
            messagebox.showwarning("Quick capture", "Unable to locate that item.")
            return
        new_text = simpledialog.askstring(
            "Edit quick capture",
            "Update the text for this entry:",
            initialvalue=item.text,
            parent=self,
        )
        if new_text is None:
            return
        new_text = new_text.strip()
        if not new_text:
            messagebox.showwarning("Quick capture", "Text cannot be empty.")
            return
        if new_text == item.text:
            return
        item.text = new_text
        self._persist()
        self._refresh_quick_capture_tree()
        self.quick_status_msg.set("Updated entry text")

    def _mock_calendar_connect(self) -> None:
        messagebox.showinfo(
            "Integrations",
            "Pretending to connect to Google Calendar. Future builds will detect conflicts and sync colors.",
        )

    def _persist(self) -> None:
        self.storage.save(self.state)


if __name__ == "__main__":
    app = ActionMenuApp()
    app.mainloop()
