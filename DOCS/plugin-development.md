# Plugin Development Guide

Complete guide to building FastCMS plugins from scratch.

## Table of Contents

- [Getting Started](#getting-started)
- [Plugin Anatomy](#plugin-anatomy)
- [Database Integration](#database-integration)
- [API Endpoints](#api-endpoints)
- [Admin UI Integration](#admin-ui-integration)
- [Frontend Components](#frontend-components)
- [Event System](#event-system)
- [Configuration](#configuration)
- [Testing](#testing)
- [Publishing](#publishing)

---

## Getting Started

### Prerequisites

- FastCMS installed and running
- Python 3.10+
- Basic knowledge of FastAPI and SQLAlchemy
- (Optional) Frontend experience for UI plugins

### Development Setup

```bash
# Navigate to FastCMS directory
cd /path/to/fastcms

# Create plugin directory
mkdir -p plugins/my_plugin
cd plugins/my_plugin

# Create virtual environment for plugin development
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Create plugin structure
touch __init__.py plugin.py config.py
```

---

## Plugin Anatomy

### Complete Plugin Example

Let's build a "Task Manager" plugin that adds TODO functionality to FastCMS.

#### File Structure

```
plugins/task_manager/
├── __init__.py           # Package initialization
├── plugin.py             # Main plugin class
├── config.py             # Configuration schema
├── models.py             # Database models
├── schemas.py            # Pydantic models
├── routes.py             # API endpoints
├── admin_routes.py       # Admin UI routes
├── services.py           # Business logic
├── templates/            # Jinja2 templates
│   ├── tasks.html
│   └── task_detail.html
├── frontend/             # Frontend assets
│   ├── TaskList.js
│   └── TaskForm.js
├── requirements.txt      # Dependencies
└── README.md             # Documentation
```

#### `__init__.py`

```python
"""Task Manager Plugin for FastCMS."""

from .plugin import TaskManagerPlugin

__version__ = "1.0.0"
__all__ = ["TaskManagerPlugin"]
```

#### `plugin.py`

```python
from app.core.plugin import BasePlugin
from fastapi import FastAPI, APIRouter
from .models import Task
from . import routes, admin_routes

class TaskManagerPlugin(BasePlugin):
    """Task management plugin."""

    # Metadata
    name = "task_manager"
    display_name = "Task Manager"
    description = "Manage tasks and to-do lists"
    version = "1.0.0"
    author = "FastCMS Team"
    homepage = "https://github.com/fastcms/plugin-task-manager"
    license = "MIT"

    # Dependencies
    requires = []  # No plugin dependencies
    depends_on = [  # Python package dependencies
        "sqlalchemy>=2.0.0",
    ]

    def initialize(self):
        """Called when plugin is loaded."""
        self.logger.info(f"Initializing {self.display_name}...")

        # Register database models
        self.register_models()

        # Initialize any resources
        self.task_service = None  # Will be initialized when needed

        self.logger.info(f"{self.display_name} initialized successfully")

    def register_models(self):
        """Register database models."""
        from app.db.base import Base
        from .models import Task

        # Models are automatically registered via SQLAlchemy Base
        self.logger.info("Task model registered")

    def register_routes(self, app: FastAPI):
        """Register API routes."""
        from . import routes

        # Include API router
        app.include_router(
            routes.router,
            prefix="/api/v1/plugins/task-manager",
            tags=["Task Manager"]
        )
        self.logger.info("API routes registered")

    def register_admin(self, admin_router: APIRouter):
        """Register admin UI routes."""
        from . import admin_routes

        # Include admin routes under /admin/plugins/task-manager
        admin_router.include_router(
            admin_routes.router,
            prefix="/plugins/task-manager"
        )
        self.logger.info("Admin routes registered")

    def shutdown(self):
        """Called when plugin is unloaded."""
        self.logger.info(f"Shutting down {self.display_name}...")
        # Cleanup resources here
```

---

## Database Integration

### Defining Models

**`models.py`:**

```python
from sqlalchemy import Column, String, Boolean, DateTime, Text, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base

class Task(Base):
    """Task model."""

    __tablename__ = "plugin_task_manager_tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    completed = Column(Boolean, default=False)
    priority = Column(String(20), default="medium")  # low, medium, high
    due_date = Column(DateTime, nullable=True)
    created = Column(DateTime, default=datetime.utcnow)
    updated = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", backref="tasks")

    def __repr__(self):
        return f"<Task {self.id}: {self.title}>"
```

### Database Migrations

Plugins can include Alembic migrations:

```bash
# Create migration
cd plugins/task_manager
alembic revision --autogenerate -m "Add task_manager tables"
```

**`migrations/versions/001_add_task_tables.py`:**

```python
"""Add task_manager tables

Revision ID: 001
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.create_table(
        'plugin_task_manager_tasks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('completed', sa.Boolean, default=False),
        sa.Column('priority', sa.String(20), default='medium'),
        sa.Column('due_date', sa.DateTime, nullable=True),
        sa.Column('created', sa.DateTime, nullable=False),
        sa.Column('updated', sa.DateTime, nullable=False),
    )

def downgrade():
    op.drop_table('plugin_task_manager_tasks')
```

---

## API Endpoints

### Creating Routes

**`routes.py`:**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List

from app.core.dependencies import require_auth, get_db
from .models import Task
from .schemas import TaskCreate, TaskUpdate, TaskResponse

router = APIRouter()

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(
    completed: bool = None,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """List all tasks for current user."""
    query = select(Task).where(Task.user_id == current_user["id"])

    if completed is not None:
        query = query.where(Task.completed == completed)

    result = await db.execute(query.order_by(Task.created.desc()))
    tasks = result.scalars().all()

    return tasks

@router.post("/tasks", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(
    task_data: TaskCreate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Create a new task."""
    task = Task(
        user_id=current_user["id"],
        **task_data.dict()
    )

    db.add(task)
    await db.commit()
    await db.refresh(task)

    return task

@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Get a specific task."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user["id"]
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    return task

@router.patch("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(
    task_id: str,
    task_data: TaskUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Update a task."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user["id"]
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Update fields
    for field, value in task_data.dict(exclude_unset=True).items():
        setattr(task, field, value)

    await db.commit()
    await db.refresh(task)

    return task

@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(
    task_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: dict = Depends(require_auth)
):
    """Delete a task."""
    result = await db.execute(
        select(Task).where(
            Task.id == task_id,
            Task.user_id == current_user["id"]
        )
    )
    task = result.scalar_one_or_none()

    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    await db.delete(task)
    await db.commit()
```

### Schemas

**`schemas.py`:**

```python
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class TaskBase(BaseModel):
    """Base task schema."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    priority: str = Field("medium", pattern="^(low|medium|high)$")
    due_date: Optional[datetime] = None

class TaskCreate(TaskBase):
    """Schema for creating a task."""
    pass

class TaskUpdate(BaseModel):
    """Schema for updating a task."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    completed: Optional[bool] = None
    priority: Optional[str] = Field(None, pattern="^(low|medium|high)$")
    due_date: Optional[datetime] = None

class TaskResponse(TaskBase):
    """Schema for task response."""
    id: str
    user_id: str
    completed: bool
    created: datetime
    updated: datetime

    class Config:
        from_attributes = True
```

---

## Admin UI Integration

### Admin Routes

**`admin_routes.py`:**

```python
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path

from app.core.dependencies import require_admin_ui
from app.core.types import UserContext

router = APIRouter()

# Setup templates
template_dir = Path(__file__).parent / "templates"
templates = Jinja2Templates(directory=str(template_dir))

@router.get("/", response_class=HTMLResponse)
async def tasks_page(
    request: Request,
    user: UserContext = Depends(require_admin_ui)
):
    """Task manager admin page."""
    return templates.TemplateResponse(
        "tasks.html",
        {
            "request": request,
            "user": user,
            "active": "task_manager"
        }
    )

@router.get("/{task_id}", response_class=HTMLResponse)
async def task_detail_page(
    request: Request,
    task_id: str,
    user: UserContext = Depends(require_admin_ui)
):
    """Task detail page."""
    return templates.TemplateResponse(
        "task_detail.html",
        {
            "request": request,
            "user": user,
            "task_id": task_id,
            "active": "task_manager"
        }
    )
```

### Adding to Navigation

Plugins can add items to the admin sidebar by providing navigation metadata:

**In `plugin.py`:**

```python
class TaskManagerPlugin(BasePlugin):
    # ... other config ...

    @property
    def navigation(self):
        """Define navigation items."""
        return {
            "label": "Tasks",
            "icon": "fa-check-square",
            "url": "/admin/plugins/task-manager",
            "section": "plugins",  # Or "main", "tools"
            "order": 100
        }
```

---

## Frontend Components

### Template Example

**`templates/tasks.html`:**

```html
{% extends "base.html" %}

{% block title %}Task Manager{% endblock %}

{% block content %}
<div x-data="taskManager()" x-init="await loadTasks()">
    <div class="px-4 sm:px-0 flex justify-between items-start">
        <div>
            <h1 class="text-3xl font-bold text-gray-900">Task Manager</h1>
            <p class="mt-2 text-sm text-gray-700">
                Manage your tasks and to-do lists
            </p>
        </div>
        <button
            @click="showCreateModal = true"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
            <i class="fas fa-plus mr-2"></i>
            New Task
        </button>
    </div>

    <!-- Task List -->
    <div class="mt-6 bg-white shadow overflow-hidden sm:rounded-lg">
        <ul class="divide-y divide-gray-200">
            <template x-for="task in tasks" :key="task.id">
                <li class="px-6 py-4 hover:bg-gray-50">
                    <div class="flex items-center justify-between">
                        <div class="flex items-center flex-1">
                            <input
                                type="checkbox"
                                :checked="task.completed"
                                @change="toggleTask(task)"
                                class="h-4 w-4 text-indigo-600 focus:ring-indigo-500 border-gray-300 rounded"
                            />
                            <div class="ml-4">
                                <h3
                                    class="text-sm font-medium"
                                    :class="{ 'line-through text-gray-400': task.completed }"
                                    x-text="task.title"
                                ></h3>
                                <p class="text-sm text-gray-500" x-text="task.description"></p>
                            </div>
                        </div>
                        <div class="flex items-center space-x-2">
                            <span
                                class="px-2 py-1 text-xs rounded"
                                :class="{
                                    'bg-red-100 text-red-800': task.priority === 'high',
                                    'bg-yellow-100 text-yellow-800': task.priority === 'medium',
                                    'bg-green-100 text-green-800': task.priority === 'low'
                                }"
                                x-text="task.priority"
                            ></span>
                            <button
                                @click="editTask(task)"
                                class="text-indigo-600 hover:text-indigo-900"
                            >
                                Edit
                            </button>
                            <button
                                @click="deleteTask(task)"
                                class="text-red-600 hover:text-red-900"
                            >
                                Delete
                            </button>
                        </div>
                    </div>
                </li>
            </template>
        </ul>
    </div>
</div>
{% endblock %}

{% block scripts %}
<script>
function taskManager() {
    return {
        tasks: [],
        showCreateModal: false,

        async loadTasks() {
            try {
                const data = await apiRequest('/plugins/task-manager/tasks');
                this.tasks = data;
            } catch (error) {
                showToast('Failed to load tasks', 'error');
            }
        },

        async toggleTask(task) {
            try {
                await apiRequest(`/plugins/task-manager/tasks/${task.id}`, {
                    method: 'PATCH',
                    body: JSON.stringify({ completed: !task.completed })
                });
                task.completed = !task.completed;
                showToast('Task updated', 'success');
            } catch (error) {
                showToast('Failed to update task', 'error');
            }
        },

        async deleteTask(task) {
            if (!confirm('Delete this task?')) return;

            try {
                await apiRequest(`/plugins/task-manager/tasks/${task.id}`, {
                    method: 'DELETE'
                });
                this.tasks = this.tasks.filter(t => t.id !== task.id);
                showToast('Task deleted', 'success');
            } catch (error) {
                showToast('Failed to delete task', 'error');
            }
        }
    };
}
</script>
{% endblock %}
```

---

## Event System

### Listening to Events

Plugins can react to FastCMS events:

```python
from app.core.events import event_bus

class TaskManagerPlugin(BasePlugin):
    def initialize(self):
        # Subscribe to events
        event_bus.subscribe("record.created", self.on_record_created)
        event_bus.subscribe("user.login", self.on_user_login)

    def on_record_created(self, event_data):
        """Handle record creation event."""
        collection = event_data.get("collection")
        record_id = event_data.get("record_id")
        self.logger.info(f"Record {record_id} created in {collection}")

    def on_user_login(self, event_data):
        """Handle user login event."""
        user_id = event_data.get("user_id")
        self.logger.info(f"User {user_id} logged in")
```

### Emitting Events

Plugins can emit their own events:

```python
from app.core.events import event_bus

# Emit event
event_bus.emit("task_manager.task_completed", {
    "task_id": task.id,
    "user_id": task.user_id,
    "completed_at": datetime.utcnow()
})
```

---

## Configuration

### Configuration Schema

**`config.py`:**

```python
from pydantic import BaseModel, Field

class TaskManagerConfig(BaseModel):
    """Task Manager plugin configuration."""

    max_tasks_per_user: int = Field(
        100,
        description="Maximum number of tasks per user"
    )
    default_priority: str = Field(
        "medium",
        description="Default task priority",
        pattern="^(low|medium|high)$"
    )
    enable_notifications: bool = Field(
        True,
        description="Enable email notifications for due tasks"
    )
    notification_days_before: int = Field(
        1,
        description="Days before due date to send notification"
    )
```

### Accessing Configuration

```python
class TaskManagerPlugin(BasePlugin):
    def get_config_schema(self):
        from .config import TaskManagerConfig
        return TaskManagerConfig

    def some_method(self):
        # Access config
        max_tasks = self.config.get("max_tasks_per_user", default=100)
        enable_notifs = self.config.get("enable_notifications", default=True)
```

---

## Testing

### Unit Tests

**`tests/test_routes.py`:**

```python
import pytest
from httpx import AsyncClient
from app.main import app

@pytest.mark.asyncio
async def test_create_task(auth_token):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/plugins/task-manager/tasks",
            json={
                "title": "Test Task",
                "description": "Test description",
                "priority": "high"
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )

    assert response.status_code == 201
    data = response.json()
    assert data["title"] == "Test Task"
    assert data["priority"] == "high"

@pytest.mark.asyncio
async def test_list_tasks(auth_token):
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/plugins/task-manager/tasks",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### Integration Tests

Test with actual database:

```python
@pytest.mark.asyncio
async def test_task_crud_flow(db_session, test_user):
    # Create
    task = Task(
        user_id=test_user.id,
        title="Integration Test Task",
        description="Test"
    )
    db_session.add(task)
    await db_session.commit()

    # Read
    result = await db_session.execute(
        select(Task).where(Task.id == task.id)
    )
    fetched = result.scalar_one()
    assert fetched.title == "Integration Test Task"

    # Update
    fetched.completed = True
    await db_session.commit()

    # Delete
    await db_session.delete(fetched)
    await db_session.commit()
```

---

## Publishing

### Packaging

**`setup.py`:**

```python
from setuptools import setup, find_packages

setup(
    name="fastcms-plugin-task-manager",
    version="1.0.0",
    author="Your Name",
    author_email="you@example.com",
    description="Task management plugin for FastCMS",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fastcms-plugin-task-manager",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    python_requires=">=3.10",
    install_requires=[
        "fastcms>=0.1.0",
        "sqlalchemy>=2.0.0",
        "fastapi>=0.100.0",
    ],
    entry_points={
        "fastcms.plugins": [
            "task_manager = task_manager.plugin:TaskManagerPlugin",
        ],
    },
)
```

### Publishing to PyPI

```bash
# Build package
python setup.py sdist bdist_wheel

# Upload to PyPI
twine upload dist/*
```

### Documentation

Include comprehensive README:

```markdown
# FastCMS Task Manager Plugin

Task management and to-do lists for FastCMS.

## Installation

```bash
pip install fastcms-plugin-task-manager
```

## Configuration

Configure via Admin UI > Settings > Plugins > Task Manager

## API Documentation

### Endpoints

- `GET /api/v1/plugins/task-manager/tasks` - List tasks
- `POST /api/v1/plugins/task-manager/tasks` - Create task
- `GET /api/v1/plugins/task-manager/tasks/{id}` - Get task
- `PATCH /api/v1/plugins/task-manager/tasks/{id}` - Update task
- `DELETE /api/v1/plugins/task-manager/tasks/{id}` - Delete task

## License

MIT
```

---

## Next Steps

- [Langflow Plugin](langflow-plugin.md) - See the Langflow integration as an example
- [Plugin Examples](https://github.com/fastcms/plugin-examples) - More examples
- [API Reference](https://fastcms.dev/api) - Complete API documentation

---

## Support

- **Issues**: https://github.com/fastcms/fastcms/issues
- **Discord**: https://discord.gg/fastcms
- **Email**: support@fastcms.dev
