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

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')
db_dependency = Annotated[Session, Depends(get_db)]
SECRET_KEY = 'QWER234DFG456CVBN543'
ALGORITHM = 'HS256'

# def create_access_token(username: str,user_id: int,role: str,expires_delta: timedelta):
#     encode = {
#         "sub": username,
#         "id": user_id,
#         "role": role
#     }
#     expires = datetime.now(timezone.utc) + expires_delta
#     encode.update({"exp": expires})
#     return jwt.encode(
#         encode,
#         SECRET_KEY,
#         algorithm=ALGORITHM
#     )

class UserRequest(BaseModel):
    manager_id:int
    name:str
    email:str
    username:str
    first_name:str
    last_name:str
    hashed_password:str
    role:str

@router.post("/create")
async def create_user(db:db_dependency,user:UserRequest):
    user.hashed_password = bcrypt_context.hash(user.hashed_password)
    final_model = Users(**user.model_dump())
    db.add(final_model)
    db.commit()
    return {"message": "User inserted!!"}

@router.get("/users")
async def get_all_users(db: db_dependency):
    return db.query(Users).all()