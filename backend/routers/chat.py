from fastapi import APIRouter
from models.chat_models import ChatRequest, ChatResponse
from services.kramer_brain import generate_kramer_reply

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/")
def chat(req: ChatRequest) -> ChatResponse:
    reply = generate_kramer_reply(req.message)
    return ChatResponse(reply=reply)
