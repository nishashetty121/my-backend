from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlmodel import Field, Session, SQLModel, create_engine, select
from pydantic import BaseModel
from auth import hash_password, verify_password, create_token, verify_token

app = FastAPI()

engine = create_engine("sqlite:///tasks.db")

# User table
class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str
    password: str

# Task table
class Task(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str

class TaskUpdate(BaseModel):
    title: str

SQLModel.metadata.create_all(engine)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# SIGNUP
@app.post("/signup")
def signup(email: str, password: str):
    with Session(engine) as session:
        hashed = hash_password(password)
        user = User(email=email, password=hashed)
        session.add(user)
        session.commit()
        return {"message": "User created!"}

# LOGIN
@app.post("/login")
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    with Session(engine) as session:
        user = session.exec(select(User).where(User.email == form_data.username)).first()
        if not user or not verify_password(form_data.password, user.password):
            raise HTTPException(status_code=401, detail="Wrong email or password")
        token = create_token({"sub": user.email})
        return {"access_token": token, "token_type": "bearer"}

# GET tasks - protected
@app.get("/tasks")
def get_tasks(token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    with Session(engine) as session:
        tasks = session.exec(select(Task)).all()
        return {"tasks": tasks}

# POST task - protected
@app.post("/tasks")
def add_task(task: Task, token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    with Session(engine) as session:
        session.add(task)
        session.commit()
        return {"message": "Task added!"}

# DELETE task - protected
@app.delete("/tasks/{task_id}")
def delete_task(task_id: int, token: str = Depends(oauth2_scheme)):
    payload = verify_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    with Session(engine) as session:
        task = session.get(Task, task_id)
        if not task:
            return {"error": "Task not found"}
        session.delete(task)
        session.commit()
        return {"message": "Task deleted!"}
