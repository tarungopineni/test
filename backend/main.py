from fastapi import FastAPI
from .routers import auth,users,tasks
from .database import Base,engine
from . import models

app = FastAPI()
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(tasks.router)

Base.metadata.create_all(bind = engine)