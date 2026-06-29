from fastapi import FastAPI
from .routers import auth
from .database import Base,engine
from . import models

app = FastAPI()
app.include_router(auth.router)

Base.metadata.create_all(bind = engine)