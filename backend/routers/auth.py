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

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

SECRET_KEY = 'QWER234DFG456CVBN543'
ALGORITHM = 'HS256'

def create_access_token(username: str,user_id: int,role: str,expires_delta: timedelta):
    encode = {
        "sub": username,
        "id": user_id,
        "role": role
    }
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(
        encode,
        SECRET_KEY,
        algorithm=ALGORITHM
    )

def authenticate(username, password, db):
    model = db.query(Users).filter(Users.username == username).first()
    if model is None:
        return None
    if not bcrypt_context.verify(password,model.hashed_password):
        return None
    return model

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM]
        )
        username = payload.get("sub")
        user_id = payload.get("id")
        user_role = payload.get("role")
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate user")
        return {
            "username": username,
            "id": user_id,
            "user_role": user_role
        }
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail="Could not validate user") 
     
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

class UserRequest(BaseModel):
    manager_id:int
    name:str
    email:str
    username:str
    first_name:str
    last_name:str
    hashed_password:str
    role:str

class TaskRequest(BaseModel):
    title:str
    description:str
    priority:str
    completed:bool
    manager_id:int
    assignee_id:int
    deadline: datetime | None = None
    deadline_text: str | None = None

@router.post("/create",status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency,user:UserRequest):
    user.hashed_password = bcrypt_context.hash(user.hashed_password)
    final_model = Users(**user.model_dump())
    db.add(final_model)
    db.commit()
    return {"message": "User inserted!!"}

@router.get("/users",status_code=status.HTTP_200_OK)
async def get_all_users(db: db_dependency):
    return db.query(Users).all()

@router.post("/token",status_code=status.HTTP_200_OK)
async def login(db: db_dependency,form_data: Annotated[OAuth2PasswordRequestForm,Depends()]):
    user = authenticate(form_data.username,form_data.password,db)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate"
        )
    token = create_access_token(
        user.username,
        user.id,
        user.role,
        timedelta(minutes=20)
    )
    return {
        "access_token": token,
        "token_type": "bearer"
    }

@router.get("/create_task",status_code=status.HTTP_201_CREATED)
async def create_task(user:user_dependency,task:TaskRequest,db:db_dependency):
    model = Tasks(
        title = task.title,
        description = task.description,
        priority = task.priority,
        manager_id = task.manager_id,
        assignee_id = task.assignee_id,
        deadline = task.deadline,
        deadline_text = task.deadline_text,
    )
    db.add(model)
    db.commit()

@router.get("/users/{user_id}",status_code=status.HTTP_200_OK)
async def get_user_by_id(db:db_dependency,user_id:int):
    model = db.query(Users).filter(Users.id == user_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    return model

@router.put("/users/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_user(user:user_dependency,db:db_dependency,req:UserRequest):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "user not authenticated")
    model = db.query(Users).filter(Users.id == user["id"]).first()
    model.manager_id = req.manager_id
    model.name = req.name
    model.email = req.email
    model.username = req.username
    model.first_name = req.first_name
    model.last_name = req.last_name
    model.hashed_password = bcrypt_context.hash(req.hashed_password)
    model.role = req.role
    db.add(model)
    db.commit()