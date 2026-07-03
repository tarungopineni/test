from fastapi import APIRouter
from ..database import SessionLocal
from passlib.context import CryptContext
from typing import Annotated, Optional
from sqlalchemy.orm import Session
from fastapi import Depends, HTTPException,Request
import datetime
from jose import jwt
from pydantic import BaseModel
from ..models import *
from starlette import status
from .auth import get_current_user

router = APIRouter(
    prefix="/users",
    tags=["users"]
)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
     
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict,Depends(get_current_user)]

class UserRequest(BaseModel):
    manager_id: Optional[int] = None
    name:str
    email:str
    username:str
    first_name:str
    last_name:str
    hashed_password:str
    role:str

@router.post("/create",status_code=status.HTTP_201_CREATED)
async def create_user(db:db_dependency,user_req:UserRequest,user:user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "user not authenticated")
    if user["role"] != "coordinator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "user not authorized")
    user_req.hashed_password = bcrypt_context.hash(user_req.hashed_password)
    final_model = Users(**user_req.model_dump())
    db.add(final_model)
    db.commit()
    return {"message": "User inserted!!"}

@router.get("/get_users",status_code=status.HTTP_200_OK)
async def get_all_users(db: db_dependency,user:user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "user not authenticated")
    if user["role"] != "coordinator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "user not authorized")
    return db.query(Users).all()

@router.get("/get_user/{user_id}",status_code=status.HTTP_200_OK)
async def get_user_by_id(db:db_dependency,user_id:int,user:user_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "user not authenticated")
    if user["role"] != "coordinator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "user not authorized")
    model = db.query(Users).filter(Users.id == user_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    return model

@router.put("/update_user/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_user(user:user_dependency,db:db_dependency,req:UserRequest,user_id:int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "user not authenticated")
    if user["role"] != "coordinator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "user not authorized")
    model = db.query(Users).filter(Users.id == user_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
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

@router.put("/update_user_manager/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def update_user_manager(user:user_dependency,db:db_dependency,manager_id: int,user_id:int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "user not authenticated")
    if user["role"] != "coordinator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "user not authorized")
    model = db.query(Users).filter(Users.id == user_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    if model.id == manager_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="user cannot be assigned to themselves")
    manager_model = db.query(Users).filter(Users.id == manager_id).first()
    if manager_model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="manager not found")
    if manager_model.manager_id == model.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="user cannot be assigned to a subordinate")
    if manager_model.role != "manager":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="provided manager_id does not belong to a manager")
    model.manager_id = manager_id
    db.add(model)
    db.commit()

@router.delete("/delete_user/{user_id}",status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(user:user_dependency,db:db_dependency,user_id:int):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "user not authenticated")
    if user["role"] != "coordinator":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "user not authorized")
    model = db.query(Users).filter(Users.id == user_id).first()
    if model is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,detail="user not found")
    db.delete(model)
    db.commit()

@router.get("/get_team",status_code=status.HTTP_200_OK)
async def get_team(user:user_dependency,db:db_dependency):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,detail = "user not authenticated")
    if user["role"] != "manager":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN,detail = "user not authorized")
    model = db.query(Users).filter(Users.manager_id == user["id"]).all()
    return model