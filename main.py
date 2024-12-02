from fastapi import FastAPI
from routes.user import user

app = FastAPI(
    title="Minha API",
    description="Documentação da API",
    version="1.0.0",
    docs_url="/docs",  # URL do Swagger
    redoc_url="/redoc",  # URL do ReDoc
    openapi_url="/openapi.json"  # URL para o esquema OpenAPI
    )

app.include_router(user)