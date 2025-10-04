# models.py
from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, declarative_base

# This Base class is what our data models will inherit from.
Base = declarative_base()

class QuickNote(Base):
    __tablename__ = "quick_notes"

    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, default="")

class Category(Base):
    """Represents a group of tasks in the database."""
    __tablename__ = "categories"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True, nullable=False)

    # This creates the one-to-many relationship.
    # A Category can have many Tasks.
    tasks = relationship("Task", back_populates="category")

    def __repr__(self):
        """Provide a developer-friendly representation of the Category object."""
        return f"<Category id={self.id} name='{self.name}'>"


class Task(Base):
    """Represents a single to-do item in the database."""
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True, nullable=False)
    points = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    priority = Column(Integer, default=0)

    # This sets up the foreign key to the 'categories' table.
    category_id = Column(Integer, ForeignKey("categories.id"))

    # This links this Task back to its parent Category.
    category = relationship("Category", back_populates="tasks")

    def __repr__(self):
        """Provide a developer-friendly representation of the Task object."""
        return f"<Task id={self.id} title='{self.title}' points={self.points} completed={self.completed}>"