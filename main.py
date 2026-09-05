import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from db import get_db_connection, init_db


@asynccontextmanager
async def lifespan(app : FastAPI):
    """Initializes the database connection and ensures the tasks table exists on application startup."""
    init_db()
    print("Database initialized and tasks table ensured.")
    yield
    print("Application shutdown.")


app= FastAPI(lifespan=lifespan)

# PYDANTIC MODELS
class TaskCreate(BaseModel):
    title: str
    done: Optional[bool] = False

@app.get('/')
def root():
    """Returns basic API metadata and the available endpoints. """
    return {
        'name': 'Task API', 
        'version' : '1.0' , 
        'endpoints' : ['/tasks'] 
        }

@app.get('/health')
def healthcheck():
    """Checks API health status."""
    return {'status' : 'ok'}

# Stage 2 Endpoints
@app.get('/tasks')
def get_tasks():
    """Returns all tasks from the PostgreSQL database."""
    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM tasks')
            tasks = cursor.fetchall()

    return tasks


@app.get('/tasks/{task_id}')
def get_task(task_id:int):
    """Retrieves a single task by its unique ID from the PostgreSQL database."""

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
            task = cursor.fetchone()
    
    if not task:
        return JSONResponse(status_code=404, content={'error': f'Task {task_id} not found'})
    
    return {
        'id': task['id'],
        'title': task['title'],
        'done': bool(task['done'])
    }

# @app.post('/tasks', status_code=201)
# def create_task(task: TaskCreate):
#     """Creates a new task with a title in the SQLite database."""
#     if not task.title or not task.title.strip():
#         return JSONResponse(status_code=400, content={'error': 'Task title cannot be empty'})

#     cursor = conn.cursor()
#     cursor.execute('INSERT INTO tasks (title, done) VALUES (?, ?)', (task.title.strip(), task.done))
#     conn.commit()

#     new_task_id = cursor.lastrowid

#     return {
#         'id': new_task_id,
#         'title': task.title.strip(),
#         'done': task.done
#     }

# class TaskUpdate(BaseModel):
#     title: Optional[str] = None
#     done: Optional[bool] = None


# @app.put('/tasks/{task_id}')
# def update_task(task_id:int, task: TaskUpdate):
#     """Updates a task's title and/or completion status."""
#     cursor = conn.cursor()
#     cursor.execute('SELECT * FROM tasks WHERE id = ?', (task_id,))
#     current_task = cursor.fetchone()
        
#     if not current_task:
#         return JSONResponse(status_code=404, content={'error': f'Task {task_id} not found'})

#     if task.title is None and task.done is None:
#         return JSONResponse(status_code=400, content={'error': 'At least one field (title or done) must be provided for update'})
    
#     if task.title is not None:
#         if not task.title.strip():
#             return JSONResponse(status_code=400, content={'error': 'Task title cannot be empty'})
#         current_task['title'] = task.title.strip()

#     new_done = current_task['done']
#     if task.done is not None:
#         new_done = task.done
    
#     cursor.execute('UPDATE tasks SET title = ?, done = ? WHERE id = ?', (current_task['title'], new_done, task_id))
#     conn.commit()

#     return {
#         'id': current_task['id'],
#         'title': current_task['title'],
#         'done': bool(current_task['done'])
#     }

# @app.delete('/tasks/{task_id}', status_code=204)
# def delete_task(task_id:int):
#     """Deletes a task by its unique ID from the SQLite database."""

#     cursor = conn.cursor()
#     cursor.execute('SELECT id FROM tasks WHERE id = ?', (task_id,))
#     task = cursor.fetchone()

#     if not task:
#         return JSONResponse(status_code=404, content={'error': f'Task {task_id} not found'})

#     cursor.execute('DELETE FROM tasks WHERE id = ?', (task_id,))
#     conn.commit()
    
#     return Response(status_code=status.HTTP_204_NO_CONTENT)
