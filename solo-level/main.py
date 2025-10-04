from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.properties import StringProperty, BooleanProperty, NumericProperty
from kivy.clock import Clock
from kivy.uix.recycleview import RecycleView
from kivy.uix.behaviors import DragBehavior

from models import Task, Category, QuickNote
from database import SessionLocal, create_db_and_tables

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

class DraggableTaskItem(DragBehavior, TaskItem):
    def on_touch_up(self, touch):
        super().on_touch_up(touch)
        if self.collide_point(*touch.pos):
            self.parent.parent.update_task_order()

class TaskList(RecycleView):
    def update_task_order(self):
        new_order = [item['task_id'] for item in self.data]
        app = App.get_running_app()
        for idx, task_id in enumerate(new_order):
            task = app.db_session.query(Task).filter(Task.id == task_id).first()
            if task:
                task.priority = idx
        app.db_session.commit()
        app.refresh_scoreboard()

class MainLayout(BoxLayout):
    pass

class SoloLevelingApp(App):
    db_session = None

    def build(self):
        create_db_and_tables()
        self.db_session = SessionLocal()
        return MainLayout()

    def on_start(self):
        self.load_data_from_db()
        Clock.schedule_once(lambda dt: self.load_notes())
        Clock.schedule_once(lambda dt: self.refresh_all_task_lists())
        Clock.schedule_interval(lambda dt: self.save_notes(), 5)

    def on_stop(self):
        self.save_notes()
        if self.db_session:
            self.db_session.close()

    def load_data_from_db(self):
        days = ["monday", "tuesday", "wednesday", "thursday",
                "friday", "saturday", "sunday"]
        for day in days:
            category_name = day.capitalize()
            category = self.db_session.query(Category).filter(Category.name == category_name).first()
            if not category:
                category = Category(name=category_name)
                self.db_session.add(category)
        self.db_session.commit()
        print("Data loaded from database.")

    def on_tab_switch(self, current_tab):
        add_bar = self.root.ids.add_task_bar
        if not current_tab:
            return
        if current_tab.text == 'Quick Notes':
            add_bar.opacity = 0
            add_bar.size_hint_y = None
            add_bar.height = 0
        else:
            add_bar.opacity = 1
            add_bar.size_hint_y = None
            add_bar.height = '48dp'
        print(f"Switched to tab: {current_tab.text}")

    def load_notes(self):
        note = self.db_session.query(QuickNote).first()
        if note:
            self.root.ids.quick_notes_input.text = note.content
        print("Quick Notes loaded.")

    def save_notes(self):
        if not self.root or 'quick_notes_input' not in self.root.ids:
            return
        notes_text = self.root.ids.quick_notes_input.text
        note = self.db_session.query(QuickNote).first()
        if note and note.content == notes_text:
            return
        if note:
            note.content = notes_text
        else:
            if not notes_text:
                return
            new_note = QuickNote(content=notes_text)
            self.db_session.add(new_note)
        self.db_session.commit()
        print("Quick Notes auto-saved.")

    def add_task(self):
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
        category_obj = self.db_session.query(Category).filter(Category.name == category_name).one()
        # Set priority as the last in the list
        max_priority = self.db_session.query(Task).filter(Task.category == category_obj).count()
        new_task = Task(
            title=title,
            points=points,
            category=category_obj,
            priority=max_priority
        )
        self.db_session.add(new_task)
        self.db_session.commit()
        self.refresh_ui_for_category(category_name.lower())
        title_input.text = ""
        points_input.text = ""

    def delete_task(self, task_id):
        task_to_delete = self.db_session.query(Task).filter(Task.id == task_id).first()
        if task_to_delete:
            category_name = task_to_delete.category.name
            self.db_session.delete(task_to_delete)
            self.db_session.commit()
            self.refresh_ui_for_category(category_name.lower())

    def toggle_task_completion(self, task_id, is_completed):
        task_to_toggle = self.db_session.query(Task).filter(Task.id == task_id).first()
        if task_to_toggle and task_to_toggle.completed is not is_completed:
            task_to_toggle.completed = is_completed
            self.db_session.commit()
            self.refresh_scoreboard()

    def refresh_ui_for_category(self, category_name):
        self.refresh_task_list(category_name)
        self.refresh_scoreboard()

    def refresh_all_task_lists(self):
        categories = self.db_session.query(Category).all()
        for category in categories:
            self.refresh_task_list(category.name.lower())
        self.refresh_scoreboard()

    def refresh_task_list(self, category_name):
        category_obj = self.db_session.query(Category).filter(Category.name == category_name.capitalize()).one()
        task_list_widget = self.root.ids.get(f"{category_name}_task_list")
        if task_list_widget:
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

    def refresh_scoreboard(self):
        total_points = sum(
            task.points for task in self.db_session.query(Task).filter(Task.completed == True).all()
        )
        self.root.ids.scoreboard_label.text = f"Total Points: {total_points}"

if __name__ == "__main__":
    SoloLevelingApp().run()
