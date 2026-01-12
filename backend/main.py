from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from routers import chat, upload, stats, visuals

app = FastAPI(title="KramerBot API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat.router)
app.include_router(upload.router)
app.include_router(stats.router)
app.include_router(visuals.router)

@app.get("/")
def root():
    return {"message": "KramerBot API running. Probably."}
