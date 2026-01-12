from fastapi import APIRouter
from pydantic import BaseModel
from models.chat_models import generate_reply

chat_router = APIRouter()

class ChatRequest(BaseModel):
    message: str

@chat_router.post("/chat")
async def chat_endpoint(req: ChatRequest):
    reply = await generate_reply(req.message)
    return {"reply": reply}
