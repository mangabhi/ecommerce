from fastapi import FastAPI
from src.utils.db import Base,engine
from src.auth.router import auth_routes

Base.metadata.create_all(engine)

app=FastAPI(title="Authentication User",description="This API will check if the user is valid or not")
app.include_router(auth_routes)


# @app.get('/')
# def firstFunc():
#     return "Here our server is running."
