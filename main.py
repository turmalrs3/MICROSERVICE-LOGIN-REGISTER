from fastapi import FastAPI
from routes.user import user

app = FastAPI(root_path="/service4")

app.include_router(user)