from fastapi import FastAPI
from routes.user import user

app = FastAPI(root_path="/service1")

app.include_router(user)