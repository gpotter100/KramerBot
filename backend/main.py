from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat_router, upload_router, stats_router, visuals_router

app = FastAPI(title="KramerBot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router) 
app.include_router(upload_router) 
app.include_router(stats_router) 
app.include_router(visuals_router)

@app.get("/")
def root():
    return {"message": "KramerBot API running. Probably."}
