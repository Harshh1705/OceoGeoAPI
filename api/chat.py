## chat api
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from services.ChatService import ChatService

router = APIRouter()
service = ChatService()
class ChatRequest(BaseModel):
    message: str

@router.post("/send_message")
async def send_message(request:ChatRequest):
    try:
        response = service.process_message(request.message)
        return {"response":response}
    except Exception as e:
        raise HTTPException(status_code=500, detail=e)