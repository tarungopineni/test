from fastapi import APIRouter
from ..database import SessionLocal
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from typing import Annotated
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException,Request
import datetime
from datetime import timezone,timedelta
from jose import jwt
from pydantic import BaseModel
from ..models import *
from jose import jwt, JWTError
from starlette import status
from .auth import get_current_user

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='tasks/token')

SECRET_KEY = 'QWER234DFG456CVBN543'
ALGORITHM = 'HS256' 
     
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

class TaskRequest(BaseModel):
    title:str
    description:str
    priority:str
    completed:bool = False
    manager_id:int
    assignee_id:int
    deadline: datetime | None = None
    deadline_text: str | None = None

class TaskStatusRequest(BaseModel):
    title:str
    description:str
    priority:str
    completed:bool

def create_task_db(task: TaskRequest, db):
    model = Tasks(
        title=task.title,
        description=task.description,
        priority=task.priority,
        manager_id=task.manager_id,
        assignee_id=task.assignee_id,
        deadline=task.deadline,
        deadline_text=task.deadline_text,
    )
    db.add(model)
    db.commit()

@router.post("/create_task",status_code=status.HTTP_201_CREATED)
async def create_task(user:user_dependency,task:TaskRequest,db:db_dependency):
    return create_task_db(task,db)

@router.get("/get_tasks",status_code=status.HTTP_200_OK)
async def get_all_tasks(user:user_dependency,db:db_dependency):
    return db.query(Tasks).all()

@router.get("/get_task/{task_id}",status_code=status.HTTP_200_OK)
async def get_task_by_id(user:user_dependency,task_id:int,db:db_dependency):
    model = db.query(Tasks).filter(Tasks.id == task_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="task not found")
    return model

@router.put("/update_task/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_task(user:user_dependency,task_id:int,task:TaskRequest,db:db_dependency):
    model = db.query(Tasks).filter(Tasks.id == task_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="task not found")
    model.title = task.title
    model.description = task.description
    model.priority = task.priority
    model.completed = task.completed
    model.manager_id = task.manager_id
    model.assignee_id = task.assignee_id
    model.deadline = task.deadline
    model.deadline_text = task.deadline_text
    db.commit()

@router.delete("/delete_task/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_task(user:user_dependency,task_id:int,db:db_dependency):
    model = db.query(Tasks).filter(Tasks.id == task_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="task not found")
    db.delete(model)
    db.commit()

@router.put("/update_task_status/{task_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_task_status(user:user_dependency,task_id:int,task:TaskStatusRequest,db:db_dependency):
    model = db.query(Tasks).filter(Tasks.id == task_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="task not found")
    model.title = task.title
    model.description = task.description
    model.priority = task.priority
    model.completed = task.completed
    db.commit()