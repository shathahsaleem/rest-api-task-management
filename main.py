from contextlib import asynccontextmanager
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
        return JSONResponse(status_code=404, content={'error': 'Task not found'})
    
    return task

# Stage 3 Endpoints
@app.post('/tasks', status_code=201)
def create_task(task: TaskCreate):
    """Creates a new task with a title in the PostgreSQL database."""
    if not task.title or not task.title.strip():
        return JSONResponse(status_code=400, content={'error': 'Task title cannot be empty'})

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('INSERT INTO tasks (title, done) VALUES (%s, %s) RETURNING *;', (task.title.strip(), task.done))
            new_task = cursor.fetchone()
        conn.commit()

    return new_task

class TaskUpdate(BaseModel):
    title: Optional[str] = None
    done: Optional[bool] = None


@app.put('/tasks/{task_id}')
def update_task(task_id:int, task: TaskUpdate):
    """Updates a task's title and/or completion status."""

    if task.title is None and task.done is None:
        return JSONResponse(status_code=400, content={'error': 'At least one field (title or done) must be provided for update'})
    
    if task.title is not None and not task.title.strip():
        return JSONResponse(status_code=400, content={'error': 'Task title cannot be empty'})

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT * FROM tasks WHERE id = %s', (task_id,))
            current_task = cursor.fetchone()
        
            if not current_task:
                return JSONResponse(status_code=404, content={'error': 'Task not found'})

            new_title = task.title.strip() if task.title is not None else current_task['title']
            new_done = task.done if task.done is not None else current_task['done']

            cursor.execute('UPDATE tasks SET title = %s, done = %s WHERE id = %s RETURNING *', (new_title, new_done, task_id))
            updated_task = cursor.fetchone()

        conn.commit()

    return updated_task


@app.delete('/tasks/{task_id}', status_code=204)
def delete_task(task_id:int):
    """Deletes a task by its unique ID from the PostgreSQL database."""

    with get_db_connection() as conn:
        with conn.cursor() as cursor:
            cursor.execute('SELECT id FROM tasks WHERE id = %s', (task_id,))
            task = cursor.fetchone()

            if not task:
                return JSONResponse(status_code=404, content={'error': 'Task not found'})

            cursor.execute('DELETE FROM tasks WHERE id = %s', (task_id,))
        conn.commit()
    
    return Response(status_code=status.HTTP_204_NO_CONTENT)
