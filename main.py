from fastapi import FastAPI
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel

app = FastAPI()

# Connect to database
engine = create_engine("sqlite:///tasks.db")

# Database table structure
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str

# For updating tasks
class TaskUpdate(BaseModel):
    title: str

# Create the table
SQLModel.metadata.create_all(engine)

# GET - fetch all tasks
@app.get("/tasks")
def get_tasks():
    with Session(engine) as session:
        tasks = session.exec(select(Task)).all()
        return {"tasks": tasks}

# POST - add a task
@app.post("/tasks")
def add_task(task: Task):
    with Session(engine) as session:
        session.add(task)
        session.commit()
        return {"message": "Task added!"}

# PUT - edit a task
@app.put("/tasks/{task_id}")
def edit_task(task_id: int, task: TaskUpdate):
    with Session(engine) as session:
        existing_task = session.get(Task, task_id)
        if not existing_task:
            return {"error": "Task not found"}
        existing_task.title = task.title
        session.add(existing_task)
        session.commit()
        return {"message": "Task edited!"}

# DELETE - delete a task
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return {"error": "Task not found"}
        session.delete(task)
        session.commit()
        return {"message": "Task deleted!"}
