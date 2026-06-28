from fastapi import FastAPI
from .routers import auth
from .database import Base,engine

app = FastAPI()
app.include_router(auth.router)

Base.metadata.create_all(bind = engine)

@app.get("/")
async def func():
    return {"Message":"end point"}