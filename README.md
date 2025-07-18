# Python Productivity App

A comprehensive task and project management application built with Python and Tkinter, featuring local storage and data visualization.

## Features

### Core Functionality
- **Task Management**: Create, edit, delete, and organize tasks
- **Project Management**: Group tasks into projects and track progress
- **Categorization**: Organize tasks by custom categories
- **Priority Levels**: Set task priorities (low, medium, high)
- **Status Tracking**: Track task status (todo, in_progress, completed)
- **Deadline Management**: Set and track due dates for tasks and projects

### User Interface
- **Tabbed Interface**: Separate tabs for tasks, projects, and analytics
- **Search and Filter**: Find tasks quickly with search and status filters
- **Context Menus**: Right-click menus for quick actions
- **Keyboard Shortcuts**: 
  - Ctrl+N: Add new task
  - Ctrl+P: Add new project
  - F5: Refresh all data

### Data Management
- **Local Storage**: SQLite database for persistent data storage
- **Data Export**: Export all data to JSON format
- **Data Import**: Import tasks and projects from JSON files
- **Progress Tracking**: Visual progress indicators for projects

### Analytics and Visualization
- **Task Statistics**: Visual charts showing task distribution by:
  - Status (pie chart)
  - Category (bar chart)
  - Priority (colored bar chart)
- **Project Progress**: Horizontal bar chart showing completion percentages

## Installation

1. Make sure you have Python 3.8+ installed
2. Install required dependencies:
   ```bash
   pip install matplotlib
