#!/usr/bin/env python3
"""
Python Productivity App - Main Entry Point
A comprehensive task and project management application with local storage.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
import json
import datetime
from typing import List, Dict, Optional
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import os


class DatabaseManager:
    """Handles all database operations for the productivity app."""

    def __init__(self, db_path: str = "productivity_app.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Initialize the database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create tasks table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                project_id INTEGER,
                status TEXT DEFAULT 'todo',
                priority TEXT DEFAULT 'medium',
                due_date TEXT,
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                completed_date TEXT,
                FOREIGN KEY (project_id) REFERENCES projects (id)
            )
        ''')

        # Create projects table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT,
                status TEXT DEFAULT 'active',
                created_date TEXT DEFAULT CURRENT_TIMESTAMP,
                due_date TEXT
            )
        ''')

        conn.commit()
        conn.close()

    def add_task(self, title: str, description: str = "", category: str = "",
                 project_id: Optional[int] = None, due_date: Optional[str] = None,
                 priority: str = "medium") -> int:
        """Add a new task to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO tasks (title, description, category, project_id, due_date, priority)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (title, description, category, project_id, due_date, priority))

        task_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return task_id

    def get_tasks(self, status: Optional[str] = None, project_id: Optional[int] = None) -> List[Dict]:
        """Retrieve tasks from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        query = '''
            SELECT t.*, p.name as project_name 
            FROM tasks t 
            LEFT JOIN projects p ON t.project_id = p.id
            WHERE 1=1
        '''
        params = []

        if status:
            query += " AND t.status = ?"
            params.append(status)

        if project_id:
            query += " AND t.project_id = ?"
            params.append(project_id)

        query += " ORDER BY t.created_date DESC"

        cursor.execute(query, params)
        columns = [description[0] for description in cursor.description]
        tasks = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return tasks

    def update_task_status(self, task_id: int, status: str):
        """Update the status of a task."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        completed_date = datetime.datetime.now().isoformat() if status == 'completed' else None

        cursor.execute('''
            UPDATE tasks 
            SET status = ?, completed_date = ?
            WHERE id = ?
        ''', (status, completed_date, task_id))

        conn.commit()
        conn.close()

    def delete_task(self, task_id: int):
        """Delete a task from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        conn.commit()
        conn.close()

    def add_project(self, name: str, description: str = "", due_date: Optional[str] = None) -> int:
        """Add a new project to the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO projects (name, description, due_date)
            VALUES (?, ?, ?)
        ''', (name, description, due_date))

        project_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return project_id

    def get_projects(self) -> List[Dict]:
        """Retrieve all projects from the database."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('''
            SELECT p.*, 
                   COUNT(t.id) as total_tasks,
                   COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks
            FROM projects p
            LEFT JOIN tasks t ON p.id = t.project_id
            GROUP BY p.id
            ORDER BY p.created_date DESC
        ''')

        columns = [description[0] for description in cursor.description]
        projects = [dict(zip(columns, row)) for row in cursor.fetchall()]

        conn.close()
        return projects

    def get_task_statistics(self) -> Dict:
        """Get task statistics for visualization."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get status counts
        cursor.execute('''
            SELECT status, COUNT(*) as count
            FROM tasks
            GROUP BY status
        ''')
        status_counts = dict(cursor.fetchall())

        # Get category counts
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM tasks
            WHERE category != ''
            GROUP BY category
        ''')
        category_counts = dict(cursor.fetchall())

        # Get priority counts
        cursor.execute('''
            SELECT priority, COUNT(*) as count
            FROM tasks
            GROUP BY priority
        ''')
        priority_counts = dict(cursor.fetchall())

        conn.close()

        return {
            'status': status_counts,
            'category': category_counts,
            'priority': priority_counts
        }


class TaskDialog:
    """Dialog for creating and editing tasks."""

    def __init__(self, parent, db_manager: DatabaseManager, task_data: Optional[Dict] = None):
        self.parent = parent
        self.db_manager = db_manager
        self.task_data = task_data
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Task" if task_data is None else "Edit Task")
        self.dialog.geometry("500x600")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()

        self.create_widgets()

        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

    def create_widgets(self):
        """Create the dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Title
        ttk.Label(main_frame, text="Title:").pack(anchor=tk.W, pady=(0, 5))
        self.title_var = tk.StringVar(value=self.task_data.get('title', '') if self.task_data else '')
        title_entry = ttk.Entry(main_frame, textvariable=self.title_var, width=50)
        title_entry.pack(fill=tk.X, pady=(0, 10))
        title_entry.focus()

        # Description
        ttk.Label(main_frame, text="Description:").pack(anchor=tk.W, pady=(0, 5))
        self.description_text = tk.Text(main_frame, height=6, width=50)
        self.description_text.pack(fill=tk.X, pady=(0, 10))
        if self.task_data:
            self.description_text.insert('1.0', self.task_data.get('description', ''))

        # Category
        ttk.Label(main_frame, text="Category:").pack(anchor=tk.W, pady=(0, 5))
        self.category_var = tk.StringVar(value=self.task_data.get('category', '') if self.task_data else '')
        category_entry = ttk.Entry(main_frame, textvariable=self.category_var, width=50)
        category_entry.pack(fill=tk.X, pady=(0, 10))

        # Priority
        ttk.Label(main_frame, text="Priority:").pack(anchor=tk.W, pady=(0, 5))
        self.priority_var = tk.StringVar(value=self.task_data.get('priority', 'medium') if self.task_data else 'medium')
        priority_combo = ttk.Combobox(main_frame, textvariable=self.priority_var,
                                      values=['low', 'medium', 'high'], state='readonly')
        priority_combo.pack(fill=tk.X, pady=(0, 10))

        # Project
        ttk.Label(main_frame, text="Project:").pack(anchor=tk.W, pady=(0, 5))
        projects = self.db_manager.get_projects()
        project_names = ['None'] + [p['name'] for p in projects]
        self.project_var = tk.StringVar(value='None')
        if self.task_data and self.task_data.get('project_name'):
            self.project_var.set(self.task_data['project_name'])

        project_combo = ttk.Combobox(main_frame, textvariable=self.project_var,
                                     values=project_names, state='readonly')
        project_combo.pack(fill=tk.X, pady=(0, 10))

        # Due Date
        ttk.Label(main_frame, text="Due Date (YYYY-MM-DD):").pack(anchor=tk.W, pady=(0, 5))
        self.due_date_var = tk.StringVar(value=self.task_data.get('due_date', '') if self.task_data else '')
        due_date_entry = ttk.Entry(main_frame, textvariable=self.due_date_var, width=50)
        due_date_entry.pack(fill=tk.X, pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT)

    def save(self):
        """Save the task data."""
        title = self.title_var.get().strip()
        if not title:
            messagebox.showerror("Error", "Title is required!")
            return

        description = self.description_text.get('1.0', tk.END).strip()
        category = self.category_var.get().strip()
        priority = self.priority_var.get()
        project_name = self.project_var.get()
        due_date = self.due_date_var.get().strip()

        # Validate due date
        if due_date:
            try:
                datetime.datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
                return

        # Get project ID
        project_id = None
        if project_name != 'None':
            projects = self.db_manager.get_projects()
            for project in projects:
                if project['name'] == project_name:
                    project_id = project['id']
                    break

        self.result = {
            'title': title,
            'description': description,
            'category': category,
            'priority': priority,
            'project_id': project_id,
            'due_date': due_date if due_date else None
        }

        self.dialog.destroy()

    def cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()


class ProjectDialog:
    """Dialog for creating and editing projects."""

    def __init__(self, parent, db_manager: DatabaseManager, project_data: Optional[Dict] = None):
        self.parent = parent
        self.db_manager = db_manager
        self.project_data = project_data
        self.result = None

        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Add Project" if project_data is None else "Edit Project")
        self.dialog.geometry("400x300")
        self.dialog.resizable(False, False)
        self.dialog.grab_set()

        self.create_widgets()

        # Center the dialog
        self.dialog.transient(parent)
        self.dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 50, parent.winfo_rooty() + 50))

    def create_widgets(self):
        """Create the dialog widgets."""
        main_frame = ttk.Frame(self.dialog, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Name
        ttk.Label(main_frame, text="Project Name:").pack(anchor=tk.W, pady=(0, 5))
        self.name_var = tk.StringVar(value=self.project_data.get('name', '') if self.project_data else '')
        name_entry = ttk.Entry(main_frame, textvariable=self.name_var, width=40)
        name_entry.pack(fill=tk.X, pady=(0, 10))
        name_entry.focus()

        # Description
        ttk.Label(main_frame, text="Description:").pack(anchor=tk.W, pady=(0, 5))
        self.description_text = tk.Text(main_frame, height=8, width=40)
        self.description_text.pack(fill=tk.X, pady=(0, 10))
        if self.project_data:
            self.description_text.insert('1.0', self.project_data.get('description', ''))

        # Due Date
        ttk.Label(main_frame, text="Due Date (YYYY-MM-DD):").pack(anchor=tk.W, pady=(0, 5))
        self.due_date_var = tk.StringVar(value=self.project_data.get('due_date', '') if self.project_data else '')
        due_date_entry = ttk.Entry(main_frame, textvariable=self.due_date_var, width=40)
        due_date_entry.pack(fill=tk.X, pady=(0, 20))

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X)

        ttk.Button(button_frame, text="Cancel", command=self.cancel).pack(side=tk.RIGHT, padx=(10, 0))
        ttk.Button(button_frame, text="Save", command=self.save).pack(side=tk.RIGHT)

    def save(self):
        """Save the project data."""
        name = self.name_var.get().strip()
        if not name:
            messagebox.showerror("Error", "Project name is required!")
            return

        description = self.description_text.get('1.0', tk.END).strip()
        due_date = self.due_date_var.get().strip()

        # Validate due date
        if due_date:
            try:
                datetime.datetime.strptime(due_date, '%Y-%m-%d')
            except ValueError:
                messagebox.showerror("Error", "Invalid date format! Use YYYY-MM-DD")
                return

        self.result = {
            'name': name,
            'description': description,
            'due_date': due_date if due_date else None
        }

        self.dialog.destroy()

    def cancel(self):
        """Cancel the dialog."""
        self.dialog.destroy()


class ProductivityApp:
    """Main application class for the Python Productivity App."""

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Python Productivity App")
        self.root.geometry("1200x800")

        # Initialize database
        self.db_manager = DatabaseManager()

        # Create GUI
        self.create_menu()
        self.create_widgets()

        # Load initial data
        self.refresh_tasks()
        self.refresh_projects()

        # Keyboard shortcuts
        self.root.bind('<Control-n>', lambda e: self.add_task())
        self.root.bind('<Control-p>', lambda e: self.add_project())
        self.root.bind('<F5>', lambda e: self.refresh_all())

    def create_menu(self):
        """Create the application menu."""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # File menu
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="File", menu=file_menu)
        file_menu.add_command(label="Export Data", command=self.export_data)
        file_menu.add_command(label="Import Data", command=self.import_data)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)

        # Edit menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Edit", menu=edit_menu)
        edit_menu.add_command(label="Add Task (Ctrl+N)", command=self.add_task)
        edit_menu.add_command(label="Add Project (Ctrl+P)", command=self.add_project)

        # View menu
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="View", menu=view_menu)
        view_menu.add_command(label="Refresh (F5)", command=self.refresh_all)

    def create_widgets(self):
        """Create the main application widgets."""
        # Create notebook for tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Tasks tab
        self.tasks_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.tasks_frame, text="Tasks")
        self.create_tasks_tab()

        # Projects tab
        self.projects_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.projects_frame, text="Projects")
        self.create_projects_tab()

        # Analytics tab
        self.analytics_frame = ttk.Frame(self.notebook)
        self.notebook.add(self.analytics_frame, text="Analytics")
        self.create_analytics_tab()

    def create_tasks_tab(self):
        """Create the tasks management tab."""
        # Toolbar
        toolbar = ttk.Frame(self.tasks_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Add Task", command=self.add_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Edit Task", command=self.edit_task).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Delete Task", command=self.delete_task).pack(side=tk.LEFT, padx=(0, 5))

        # Status filter
        ttk.Label(toolbar, text="Filter by Status:").pack(side=tk.LEFT, padx=(20, 5))
        self.status_filter_var = tk.StringVar(value="All")
        status_combo = ttk.Combobox(toolbar, textvariable=self.status_filter_var,
                                    values=["All", "todo", "in_progress", "completed"],
                                    state="readonly", width=15)
        status_combo.pack(side=tk.LEFT, padx=(0, 5))
        status_combo.bind('<<ComboboxSelected>>', self.filter_tasks)

        # Search
        ttk.Label(toolbar, text="Search:").pack(side=tk.LEFT, padx=(20, 5))
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(toolbar, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT, padx=(0, 5))
        search_entry.bind('<KeyRelease>', self.filter_tasks)

        ttk.Button(toolbar, text="Refresh", command=self.refresh_tasks).pack(side=tk.RIGHT)

        # Tasks list
        list_frame = ttk.Frame(self.tasks_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview
        columns = ("ID", "Title", "Category", "Project", "Priority", "Status", "Due Date", "Created")
        self.tasks_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        # Configure columns
        self.tasks_tree.heading("ID", text="ID")
        self.tasks_tree.heading("Title", text="Title")
        self.tasks_tree.heading("Category", text="Category")
        self.tasks_tree.heading("Project", text="Project")
        self.tasks_tree.heading("Priority", text="Priority")
        self.tasks_tree.heading("Status", text="Status")
        self.tasks_tree.heading("Due Date", text="Due Date")
        self.tasks_tree.heading("Created", text="Created")

        self.tasks_tree.column("ID", width=50)
        self.tasks_tree.column("Title", width=200)
        self.tasks_tree.column("Category", width=100)
        self.tasks_tree.column("Project", width=100)
        self.tasks_tree.column("Priority", width=80)
        self.tasks_tree.column("Status", width=100)
        self.tasks_tree.column("Due Date", width=100)
        self.tasks_tree.column("Created", width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.tasks_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.tasks_tree.xview)
        self.tasks_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.tasks_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Context menu
        self.tasks_context_menu = tk.Menu(self.root, tearoff=0)
        self.tasks_context_menu.add_command(label="Mark as Todo", command=lambda: self.change_task_status("todo"))
        self.tasks_context_menu.add_command(label="Mark as In Progress",
                                            command=lambda: self.change_task_status("in_progress"))
        self.tasks_context_menu.add_command(label="Mark as Completed",
                                            command=lambda: self.change_task_status("completed"))
        self.tasks_context_menu.add_separator()
        self.tasks_context_menu.add_command(label="Edit Task", command=self.edit_task)
        self.tasks_context_menu.add_command(label="Delete Task", command=self.delete_task)

        self.tasks_tree.bind("<Button-3>", self.show_tasks_context_menu)
        self.tasks_tree.bind("<Double-1>", lambda e: self.edit_task())

    def create_projects_tab(self):
        """Create the projects management tab."""
        # Toolbar
        toolbar = ttk.Frame(self.projects_frame)
        toolbar.pack(fill=tk.X, padx=5, pady=5)

        ttk.Button(toolbar, text="Add Project", command=self.add_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Edit Project", command=self.edit_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Delete Project", command=self.delete_project).pack(side=tk.LEFT, padx=(0, 5))
        ttk.Button(toolbar, text="Refresh", command=self.refresh_projects).pack(side=tk.RIGHT)

        # Projects list
        list_frame = ttk.Frame(self.projects_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Create treeview
        columns = ("ID", "Name", "Description", "Total Tasks", "Completed", "Progress", "Due Date", "Created")
        self.projects_tree = ttk.Treeview(list_frame, columns=columns, show="headings", height=15)

        # Configure columns
        for col in columns:
            self.projects_tree.heading(col, text=col)

        self.projects_tree.column("ID", width=50)
        self.projects_tree.column("Name", width=150)
        self.projects_tree.column("Description", width=200)
        self.projects_tree.column("Total Tasks", width=100)
        self.projects_tree.column("Completed", width=100)
        self.projects_tree.column("Progress", width=80)
        self.projects_tree.column("Due Date", width=100)
        self.projects_tree.column("Created", width=120)

        # Scrollbars
        v_scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=self.projects_tree.yview)
        h_scrollbar = ttk.Scrollbar(list_frame, orient=tk.HORIZONTAL, command=self.projects_tree.xview)
        self.projects_tree.configure(yscrollcommand=v_scrollbar.set, xscrollcommand=h_scrollbar.set)

        # Pack treeview and scrollbars
        self.projects_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        v_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        h_scrollbar.pack(side=tk.BOTTOM, fill=tk.X)

        # Context menu
        self.projects_context_menu = tk.Menu(self.root, tearoff=0)
        self.projects_context_menu.add_command(label="View Tasks", command=self.view_project_tasks)
        self.projects_context_menu.add_command(label="Edit Project", command=self.edit_project)
        self.projects_context_menu.add_command(label="Delete Project", command=self.delete_project)

        self.projects_tree.bind("<Button-3>", self.show_projects_context_menu)
        self.projects_tree.bind("<Double-1>", lambda e: self.view_project_tasks())

    def create_analytics_tab(self):
        """Create the analytics and visualization tab."""
        # Create canvas for matplotlib
        self.analytics_canvas_frame = ttk.Frame(self.analytics_frame)
        self.analytics_canvas_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        # Refresh button
        refresh_frame = ttk.Frame(self.analytics_frame)
        refresh_frame.pack(fill=tk.X, padx=5, pady=5)
        ttk.Button(refresh_frame, text="Refresh Charts", command=self.refresh_analytics).pack(side=tk.RIGHT)

        self.refresh_analytics()

    def add_task(self):
        """Open dialog to add a new task."""
        dialog = TaskDialog(self.root, self.db_manager)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            self.db_manager.add_task(**dialog.result)
            self.refresh_tasks()
            messagebox.showinfo("Success", "Task added successfully!")

    def edit_task(self):
        """Open dialog to edit the selected task."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to edit.")
            return

        task_id = self.tasks_tree.item(selection[0])['values'][0]
        tasks = self.db_manager.get_tasks()
        task_data = next((task for task in tasks if task['id'] == task_id), None)

        if task_data:
            dialog = TaskDialog(self.root, self.db_manager, task_data)
            self.root.wait_window(dialog.dialog)

            if dialog.result:
                # Update task in database (you'd need to implement update_task method)
                messagebox.showinfo("Info", "Task editing not fully implemented yet.")
                self.refresh_tasks()

    def delete_task(self):
        """Delete the selected task."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this task?"):
            task_id = self.tasks_tree.item(selection[0])['values'][0]
            self.db_manager.delete_task(task_id)
            self.refresh_tasks()
            messagebox.showinfo("Success", "Task deleted successfully!")

    def change_task_status(self, status: str):
        """Change the status of the selected task."""
        selection = self.tasks_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a task.")
            return

        task_id = self.tasks_tree.item(selection[0])['values'][0]
        self.db_manager.update_task_status(task_id, status)
        self.refresh_tasks()

    def add_project(self):
        """Open dialog to add a new project."""
        dialog = ProjectDialog(self.root, self.db_manager)
        self.root.wait_window(dialog.dialog)

        if dialog.result:
            self.db_manager.add_project(**dialog.result)
            self.refresh_projects()
            messagebox.showinfo("Success", "Project added successfully!")

    def edit_project(self):
        """Open dialog to edit the selected project."""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project to edit.")
            return

        messagebox.showinfo("Info", "Project editing not fully implemented yet.")

    def delete_project(self):
        """Delete the selected project."""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project to delete.")
            return

        if messagebox.askyesno("Confirm", "Are you sure you want to delete this project and all its tasks?"):
            messagebox.showinfo("Info", "Project deletion not fully implemented yet.")

    def view_project_tasks(self):
        """Show tasks for the selected project."""
        selection = self.projects_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a project.")
            return

        project_id = self.projects_tree.item(selection[0])['values'][0]
        self.status_filter_var.set("All")
        self.search_var.set("")

        # Switch to tasks tab and filter by project
        self.notebook.select(0)  # Select tasks tab
        tasks = self.db_manager.get_tasks(project_id=project_id)
        self.populate_tasks_tree(tasks)

    def show_tasks_context_menu(self, event):
        """Show context menu for tasks."""
        item = self.tasks_tree.identify_row(event.y)
        if item:
            self.tasks_tree.selection_set(item)
            self.tasks_context_menu.post(event.x_root, event.y_root)

    def show_projects_context_menu(self, event):
        """Show context menu for projects."""
        item = self.projects_tree.identify_row(event.y)
        if item:
            self.projects_tree.selection_set(item)
            self.projects_context_menu.post(event.x_root, event.y_root)

    def filter_tasks(self, event=None):
        """Filter tasks based on status and search criteria."""
        status_filter = self.status_filter_var.get()
        search_text = self.search_var.get().lower()

        # Get tasks with filter
        status = None if status_filter == "All" else status_filter
        tasks = self.db_manager.get_tasks(status=status)

        # Apply search filter
        if search_text:
            tasks = [task for task in tasks if
                     search_text in task['title'].lower() or
                     search_text in (task['description'] or '').lower() or
                     search_text in (task['category'] or '').lower()]

        self.populate_tasks_tree(tasks)

    def refresh_tasks(self):
        """Refresh the tasks list."""
        self.filter_tasks()

    def refresh_projects(self):
        """Refresh the projects list."""
        projects = self.db_manager.get_projects()
        self.populate_projects_tree(projects)

    def refresh_analytics(self):
        """Refresh the analytics charts."""
        # Clear previous charts
        for widget in self.analytics_canvas_frame.winfo_children():
            widget.destroy()

        stats = self.db_manager.get_task_statistics()

        # Create figure with subplots
        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 8))
        fig.suptitle('Task Analytics', fontsize=16)

        # Status distribution pie chart
        if stats['status']:
            ax1.pie(stats['status'].values(), labels=stats['status'].keys(), autopct='%1.1f%%')
            ax1.set_title('Tasks by Status')
        else:
            ax1.text(0.5, 0.5, 'No tasks available', ha='center', va='center')
            ax1.set_title('Tasks by Status')

        # Category distribution bar chart
        if stats['category']:
            ax2.bar(stats['category'].keys(), stats['category'].values())
            ax2.set_title('Tasks by Category')
            ax2.tick_params(axis='x', rotation=45)
        else:
            ax2.text(0.5, 0.5, 'No categories available', ha='center', va='center')
            ax2.set_title('Tasks by Category')

        # Priority distribution
        if stats['priority']:
            ax3.bar(stats['priority'].keys(), stats['priority'].values(),
                    color=['green', 'orange', 'red'])
            ax3.set_title('Tasks by Priority')
        else:
            ax3.text(0.5, 0.5, 'No priorities available', ha='center', va='center')
            ax3.set_title('Tasks by Priority')

        # Project progress (placeholder)
        projects = self.db_manager.get_projects()
        if projects:
            project_names = [p['name'][:10] + '...' if len(p['name']) > 10 else p['name'] for p in projects[:5]]
            progress_values = [p['completed_tasks'] / max(p['total_tasks'], 1) * 100 for p in projects[:5]]
            ax4.barh(project_names, progress_values)
            ax4.set_title('Project Progress (%)')
            ax4.set_xlim(0, 100)
        else:
            ax4.text(0.5, 0.5, 'No projects available', ha='center', va='center')
            ax4.set_title('Project Progress (%)')

        plt.tight_layout()

        # Embed in tkinter
        canvas = FigureCanvasTkAgg(fig, self.analytics_canvas_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def refresh_all(self):
        """Refresh all data."""
        self.refresh_tasks()
        self.refresh_projects()
        self.refresh_analytics()

    def populate_tasks_tree(self, tasks: List[Dict]):
        """Populate the tasks treeview with data."""
        # Clear existing items
        for item in self.tasks_tree.get_children():
            self.tasks_tree.delete(item)

        # Add tasks
        for task in tasks:
            created_date = task['created_date'][:10] if task['created_date'] else ''
            due_date = task['due_date'] if task['due_date'] else ''
            project_name = task.get('project_name', '') or ''

            self.tasks_tree.insert('', 'end', values=(
                task['id'],
                task['title'],
                task['category'] or '',
                project_name,
                task['priority'],
                task['status'],
                due_date,
                created_date
            ))

    def populate_projects_tree(self, projects: List[Dict]):
        """Populate the projects treeview with data."""
        # Clear existing items
        for item in self.projects_tree.get_children():
            self.projects_tree.delete(item)

        # Add projects
        for project in projects:
            created_date = project['created_date'][:10] if project['created_date'] else ''
            due_date = project['due_date'] if project['due_date'] else ''
            total_tasks = project['total_tasks'] or 0
            completed_tasks = project['completed_tasks'] or 0
            progress = f"{completed_tasks}/{total_tasks}"

            self.projects_tree.insert('', 'end', values=(
                project['id'],
                project['name'],
                project['description'] or '',
                total_tasks,
                completed_tasks,
                progress,
                due_date,
                created_date
            ))

    def export_data(self):
        """Export data to JSON file."""
        try:
            filename = filedialog.asksaveasfilename(
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                tasks = self.db_manager.get_tasks()
                projects = self.db_manager.get_projects()

                data = {
                    'tasks': tasks,
                    'projects': projects,
                    'exported_at': datetime.datetime.now().isoformat()
                }

                with open(filename, 'w') as f:
                    json.dump(data, f, indent=2)

                messagebox.showinfo("Success", f"Data exported to {filename}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export data: {str(e)}")

    def import_data(self):
        """Import data from JSON file."""
        try:
            filename = filedialog.askopenfilename(
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )

            if filename:
                if messagebox.askyesno("Confirm", "This will add imported data to existing data. Continue?"):
                    with open(filename, 'r') as f:
                        data = json.load(f)

                    # Import projects first
                    if 'projects' in data:
                        for project in data['projects']:
                            self.db_manager.add_project(
                                project['name'],
                                project.get('description', ''),
                                project.get('due_date')
                            )

                    # Import tasks
                    if 'tasks' in data:
                        for task in data['tasks']:
                            self.db_manager.add_task(
                                task['title'],
                                task.get('description', ''),
                                task.get('category', ''),
                                task.get('project_id'),
                                task.get('due_date'),
                                task.get('priority', 'medium')
                            )

                    self.refresh_all()
                    messagebox.showinfo("Success", "Data imported successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import data: {str(e)}")

    def run(self):
        """Start the application."""
        self.root.mainloop()


if __name__ == "__main__":
    app = ProductivityApp()
    app.run()