# backend/main.py

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers.chat import chat_router
from routers.upload import router as upload_router
from routers.stats import router as stats_router
from routers.visuals import router as visuals_router

app = FastAPI(title="KramerBot API", version="0.1.0")

# Read allowed origins from environment (Render)
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "*").split(",")

print("🚀 Allowed CORS origins:", allowed_origins)

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(chat_router)
app.include_router(upload_router)
app.include_router(stats_router)
app.include_router(visuals_router)

@app.get("/")
def root():
    return {"message": "KramerBot API running. Probably."}
