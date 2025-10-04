# C:/Anirudh/solo-level/models.py

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    Boolean,
    Text,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, relationship, Mapped, mapped_column
from typing import List

# Base class for our models. All model classes will inherit from this.
Base = declarative_base()


class Category(Base):
    """
    Represents a category for tasks, e.g., 'Monday', 'Tuesday'.
    """
    __tablename__ = "categories"

    # Using Mapped and mapped_column for modern, type-annotated definitions.
    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)

    # Establishes a one-to-many relationship with the Task model.
    # 'cascade' ensures that when a category is deleted, its tasks are also deleted.
    # 'back_populates' links this relationship to the 'category' attribute in Task.
    tasks: Mapped[List["Task"]] = relationship(
        back_populates="category", cascade="all, delete-orphan"
    )

    def __repr__(self):
        """Provides a developer-friendly string representation of the object."""
        return f"<Category(id={self.id}, name='{self.name}')>"


class Task(Base):
    """
    Represents a single task item.
    """
    __tablename__ = "tasks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String, nullable=False)
    points: Mapped[int] = mapped_column(Integer, default=0)
    completed: Mapped[bool] = mapped_column(Boolean, default=False)
    priority: Mapped[int] = mapped_column(Integer, default=0) # For ordering

    # Establishes a many-to-one relationship with the Category model.
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), nullable=False)
    category: Mapped["Category"] = relationship(back_populates="tasks")

    def __repr__(self):
        """Provides a developer-friendly string representation of the object."""
        return f"<Task(id={self.id}, title='{self.title}', completed={self.completed})>"


class QuickNote(Base):
    """
    Represents a single, persistent quick note.
    """
    __tablename__ = "quick_notes"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Using Text instead of String for potentially long notes.
    content: Mapped[str] = mapped_column(Text, default="")

    def __repr__(self):
        """Provides a developer-friendly string representation of the object."""
        return f"<QuickNote(id={self.id}, content='{self.content[:30]}...')>"
