# C:/Anirudh/solo-level/main.py

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.recycleview import RecycleView
from kivy.uix.behaviors import DragBehavior
from sqlalchemy.orm import Session

from models import Task, Category, QuickNote
from database import SessionLocal, create_db_and_tables


# --- Widget Classes ---

class TaskItem(RecycleDataViewBehavior, BoxLayout):
    """A view for a single task in the RecycleView."""
    task_id = NumericProperty()
    title = StringProperty()
    points = NumericProperty()
    completed = BooleanProperty(False)

    __events__ = ('on_toggle_complete', 'on_delete_task')

    def refresh_view_attrs(self, rv, index, data):
        """Standard method to update the view from data."""
        for key in list(data.keys()):
            if not hasattr(self, key):
                del data[key]
        return super().refresh_view_attrs(rv, index, data)

    def on_toggle_complete(self, value: bool):
        """Event handler stub for toggling task completion."""
        pass

    def on_delete_task(self):
        """Event handler stub for deleting a task."""
        pass


class DraggableTaskItem(DragBehavior, TaskItem):
    """A TaskItem that can be dragged and dropped to reorder."""

    def on_touch_up(self, touch):
        """Handle the end of a drag gesture to trigger reordering."""
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            if app and hasattr(app.root, 'ids'):
                # Find the parent TaskList by checking the parent of the RecycleView's layout
                rv_layout_parent = self.parent.parent
                for task_list_id in app.root.ids:
                    widget = app.root.ids[task_list_id]
                    if isinstance(widget, TaskList) and widget.parent == rv_layout_parent:
                        widget.update_task_order()
                        break
        return super().on_touch_up(touch)


class TaskList(RecycleView):
    """A RecycleView for displaying and managing a list of tasks."""

    def update_task_order(self):
        """
        Updates the priority of tasks in the database based on their
        current order in the UI. This version is optimized to reduce DB queries.
        """
        app = App.get_running_app()
        if not app or not self.data:
            return

        task_ids_in_view = [item['task_id'] for item in self.data]

        # Using a context manager for the session is a good practice,
        # but since the app uses a single long-lived session, we'll stick to that pattern.
        tasks_to_update = app.db_session.query(Task).filter(Task.id.in_(task_ids_in_view)).all()
        task_map = {task.id: task for task in tasks_to_update}

        for new_priority, item_data in enumerate(self.data):
            task = task_map.get(item_data['task_id'])
            if task and task.priority != new_priority:
                task.priority = new_priority

        app.db_session.commit()
        app.refresh_scoreboard()
        print("Task order updated.")


class MainLayout(BoxLayout):
    """The root widget of the application, defined in the .kv file."""
    pass


# --- Main Application Class ---

class SoloLevelingApp(App):
    """The main application class."""
    # --- Constants ---
    # Moved inside the class to be accessible from the .kv file via `app.`
    DAYS_OF_WEEK = ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"]
    QUICK_NOTES_TAB_TEXT = 'Quick Notes'

    db_session: Session = None

    def build(self):
        """Initializes the database and returns the root widget."""
        create_db_and_tables()
        self.db_session = SessionLocal()
        return MainLayout()

    def on_start(self):
        """Loads initial data and schedules recurring tasks."""
        self.load_initial_categories()
        Clock.schedule_once(self._post_build_init)
        Clock.schedule_interval(self.save_notes, 5)

    def _post_build_init(self, dt):
        """Tasks to run after the UI is fully constructed."""
        self.load_notes()
        self.refresh_all_task_lists()

    def on_stop(self):
        """Saves final data and closes the database session."""
        self.save_notes()
        if self.db_session:
            self.db_session.close()
            print("Database session closed.")

    def load_initial_categories(self):
        """Ensures all day categories exist in the database."""
        existing_categories = {cat.name for cat in self.db_session.query(Category.name).all()}
        for day in self.DAYS_OF_WEEK:
            category_name = day.capitalize()
            if category_name not in existing_categories:
                self.db_session.add(Category(name=category_name))
        self.db_session.commit()
        print("Categories initialized.")

    def on_tab_switch(self, current_tab):
        """Hides or shows the 'add task' bar based on the selected tab."""
        if not hasattr(self.root, 'ids') or not current_tab:
            return

        add_bar = self.root.ids.add_task_bar
        is_notes_tab = current_tab.text == self.QUICK_NOTES_TAB_TEXT

        add_bar.opacity = 0 if is_notes_tab else 1
        add_bar.height = 0 if is_notes_tab else '48dp'
        add_bar.size_hint_y = None

    def load_notes(self):
        """Loads content into the Quick Notes input."""
        note = self.db_session.query(QuickNote).first()
        if note:
            self.root.ids.quick_notes_input.text = note.content
        print("Quick Notes loaded.")

    def save_notes(self, *args):
        """Saves the content of the Quick Notes input to the database."""
        if not self.root or 'quick_notes_input' not in self.root.ids:
            return

        notes_text = self.root.ids.quick_notes_input.text
        note = self.db_session.query(QuickNote).first()

        if note:
            if note.content != notes_text:
                note.content = notes_text
                self.db_session.commit()
                print("Quick Notes updated.")
        elif notes_text:
            new_note = QuickNote(content=notes_text)
            self.db_session.add(new_note)
            self.db_session.commit()
            print("Quick Notes saved.")

    def add_task(self):
        """Adds a new task to the current category."""
        title_input = self.root.ids.task_title_input
        points_input = self.root.ids.task_points_input
        title = title_input.text.strip()

        if not title:
            return

        main_tabs = self.root.ids.main_tabs
        if not main_tabs.current_tab:
            main_tabs.switch_to(main_tabs.tab_list[0])

        category_name = main_tabs.current_tab.text
        category_obj = self.db_session.query(Category).filter_by(name=category_name).one()

        try:
            points = int(points_input.text or 0)
        except ValueError:
            points = 0

        max_priority = self.db_session.query(Task).filter_by(category_id=category_obj.id).count()

        new_task = Task(title=title, points=points, category_id=category_obj.id, priority=max_priority)
        self.db_session.add(new_task)
        self.db_session.commit()

        self.refresh_ui_for_category(category_name.lower())
        title_input.text = ""
        points_input.text = ""
        print(f"Task '{title}' added to {category_name}.")

    def delete_task(self, task_id: int):
        """Deletes a task from the database."""
        task_to_delete = self.db_session.get(Task, task_id)
        if task_to_delete:
            category_name = task_to_delete.category.name
            self.db_session.delete(task_to_delete)
            self.db_session.commit()
            self.refresh_ui_for_category(category_name.lower())
            print(f"Task ID {task_id} deleted.")

    def toggle_task_completion(self, task_id: int, is_completed: bool):
        """Toggles the completion status of a task."""
        task_to_toggle = self.db_session.get(Task, task_id)
        if task_to_toggle and task_to_toggle.completed is not is_completed:
            task_to_toggle.completed = is_completed
            self.db_session.commit()
            self.refresh_scoreboard()

    def refresh_ui_for_category(self, category_name: str):
        """Refreshes the task list and scoreboard for a given category."""
        self.refresh_task_list(category_name)
        self.refresh_scoreboard()

    def refresh_all_task_lists(self):
        """Refreshes all task lists and the scoreboard."""
        for day in self.DAYS_OF_WEEK:
            self.refresh_task_list(day)
        self.refresh_scoreboard()

    def refresh_task_list(self, category_name: str):
        """Updates the data in a specific category's RecycleView."""
        task_list_widget = self.root.ids.get(f"{category_name}_task_list")
        if not task_list_widget:
            return

        category_obj = self.db_session.query(Category).filter(Category.name == category_name.capitalize()).one()

        sorted_tasks = sorted(category_obj.tasks, key=lambda t: t.priority)

        task_list_widget.data = [
            {
                "task_id": task.id,
                "title": task.title,
                "points": task.points,
                "completed": task.completed,
                'on_toggle_complete': lambda val, t_id=task.id: self.toggle_task_completion(t_id, val),
                'on_delete_task': lambda t_id=task.id: self.delete_task(t_id)
            }
            for task in sorted_tasks
        ]
        task_list_widget.refresh_from_data()

    def refresh_scoreboard(self):
        """Updates the total points display."""
        total_points = sum(
            task.points for task in self.db_session.query(Task).filter_by(completed=True)
        ) or 0
        self.root.ids.scoreboard_label.text = f"Total Points: {total_points}"


if __name__ == "__main__":
    SoloLevelingApp().run()