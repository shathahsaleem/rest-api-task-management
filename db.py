import os
from dotenv import load_dotenv
import time
import psycopg
from psycopg.rows import dict_row

load_dotenv()

def get_db_connection():
    """Establishes an active connection to the PostgreSQL container with dict rows."""
    DATABASE_URL = os.getenv('DATABASE_URL')
    return psycopg.connect(DATABASE_URL, row_factory=dict_row)

def init_db():
    """Ensures the tasks table exists in PostgreSQL on application startup."""
    retries = 5
    while retries > 0:
        try:
            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    cursor.execute(
                        '''
                        CREATE TABLE IF NOT EXISTS tasks (
                            id SERIAL PRIMARY KEY,
                            title text NOT NULL,
                            done BOOLEAN NOT NULL DEFAULT FALSE
                        )
                        '''
                    )
                
                    cursor.execute('SELECT COUNT(*) as count FROM tasks')
                    count = cursor.fetchone()['count']

                    if count == 0:
                        seed_tasks = [
                            ('Buy groceries', True),
                            ('Clean the house', False),
                            ('Cook dinner', False)
                        ]
                        cursor.executemany('INSERT INTO tasks (title, done) VALUES (%s, %s)', seed_tasks)
                
                conn.commit()
                print("Database initialized successfully.")
            return
        except psycopg.OperationalError:
            print("Database connection failed. Retrying in 2 seconds...")
            retries -= 1
            time.sleep(2)
    raise Exception("Failed to connect to the database after multiple attempts.")