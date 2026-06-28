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