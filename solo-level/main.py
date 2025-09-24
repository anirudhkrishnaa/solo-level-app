# C:/Anirudh/solo-level/main.py

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.recycleview import RecycleView

# --- Database Integration ---
from models import Task, Category
from database import SessionLocal, create_db_and_tables


# -------------------------
# UI Widgets
# -------------------------
class TaskItem(RecycleDataViewBehavior, BoxLayout):
    task_id = NumericProperty()
    title = StringProperty()
    points = NumericProperty()
    completed = BooleanProperty(False)
    __events__ = ('on_toggle_complete', 'on_delete_task')

    def refresh_view_attrs(self, rv, index, data):
        for key, value in data.items():
            setattr(self, key, value)
        return super().refresh_view_attrs(rv, index, data)

    def on_toggle_complete(self, value):
        pass

    def on_delete_task(self):
        pass


class TaskList(RecycleView):
    pass


class MainLayout(BoxLayout):
    pass


# -------------------------
# Main App
# -------------------------
class SoloLevelingApp(App):
    # --- Database Session ---
    db_session = None

    def build(self):
        # --- Database Setup ---
        # 1. Create the database file and tables if they don't exist
        create_db_and_tables()
        # 2. Create a session to interact with the database
        self.db_session = SessionLocal()

        return MainLayout()

    def on_start(self):
        """Load data from the database and populate the UI."""
        self.load_data_from_db()
        Clock.schedule_once(lambda dt: self.refresh_all_task_lists())

    def on_stop(self):
        """Close the database session when the app closes."""
        if self.db_session:
            self.db_session.close()

    # -------------------------
    # Data Loading
    # -------------------------
    def load_data_from_db(self):
        """Initializes categories and loads all tasks from the database."""
        days = ["monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday"]

        for day in days:
            category_name = day.capitalize()
            # Check if the category already exists in the DB
            category = self.db_session.query(Category).filter(Category.name == category_name).first()
            if not category:
                # FIX: Use keyword argument `name=`
                category = Category(name=category_name)
                self.db_session.add(category)

        # Commit all new categories at once
        self.db_session.commit()

        # The UI will be refreshed in on_start
        print("Data loaded from database.")

    # -------------------------
    # Task & State Management
    # -------------------------
    def add_task(self):
        """Adds a new task to the database and updates the UI."""
        title_input = self.root.ids.task_title_input
        points_input = self.root.ids.task_points_input

        if not self.root.ids.main_tabs.current_tab:
            self.root.ids.main_tabs.switch_to(self.root.ids.main_tabs.tab_list[0])

        category_name = self.root.ids.main_tabs.current_tab.text
        title = title_input.text.strip()
        if not title:
            return

        try:
            points = int(points_input.text or 0)
        except ValueError:
            points = 0

        # Get the category object from the database
        category_obj = self.db_session.query(Category).filter(Category.name == category_name).one()

        # FIX: Use keyword arguments and pass the category object
        new_task = Task(
            title=title,
            points=points,
            category=category_obj  # Associate with the Category object
        )

        self.db_session.add(new_task)
        self.db_session.commit()

        self.refresh_ui_for_category(category_name.lower())

        title_input.text = ""
        points_input.text = ""

    def delete_task(self, task_id):
        """Deletes a task from the database by its ID."""
        task_to_delete = self.db_session.query(Task).filter(Task.id == task_id).first()
        if task_to_delete:
            category_name = task_to_delete.category.name
            self.db_session.delete(task_to_delete)
            self.db_session.commit()
            self.refresh_ui_for_category(category_name.lower())

    def toggle_task_completion(self, task_id, is_completed):
        """Toggles the completion status of a task in the database."""
        task_to_toggle = self.db_session.query(Task).filter(Task.id == task_id).first()
        if task_to_toggle and task_to_toggle.completed is not is_completed:
            task_to_toggle.completed = is_completed
            self.db_session.commit()
            self.refresh_scoreboard()  # Only need to refresh scoreboard, not the whole list

    # -------------------------
    # UI Update Helpers
    # -------------------------
    def refresh_ui_for_category(self, category_name):
        """Refreshes the task list for a specific category and the scoreboard."""
        self.refresh_task_list(category_name)
        self.refresh_scoreboard()

    def refresh_all_task_lists(self):
        """Updates every task list in the TabbedPanel."""
        categories = self.db_session.query(Category).all()
        for category in categories:
            self.refresh_task_list(category.name.lower())
        self.refresh_scoreboard()

    def refresh_task_list(self, category_name):
        """Updates the data for a single category's RecycleView from the database."""
        category_obj = self.db_session.query(Category).filter(Category.name == category_name.capitalize()).one()
        task_list_widget = self.root.ids.get(f"{category_name}_task_list")

        if task_list_widget:
            # Sort tasks by their database ID
            sorted_tasks = sorted(category_obj.tasks, key=lambda t: t.id)
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

    def refresh_scoreboard(self):
        """Updates the scoreboard with the total points from completed tasks in the DB."""
        total_points = sum(
            task.points for task in self.db_session.query(Task).filter(Task.completed == True).all()
        )
        self.root.ids.scoreboard_label.text = f"Total Points: {total_points}"


# -------------------------
# Run App
# -------------------------
if __name__ == "__main__":
    SoloLevelingApp().run()