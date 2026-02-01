"""Chat system models"""

from enum import Enum
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class ChatMode(str, Enum):
    """Chat interaction mode"""
    TUTOR = "tutor"
    EDITOR = "editor"


class ChatMessage(BaseModel):
    """Chat message"""
    message_id: str
    job_id: str
    pdf_version: str
    role: str = Field(..., description="user or assistant")
    content: str
    mode: ChatMode = Field(default=ChatMode.TUTOR)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    # For assistant responses
    citations: Optional[List[str]] = None  # PDF sections referenced
    edit_applied: bool = False
    
    class Config:
        json_schema_extra = {
            "example": {
                "message_id": "msg_001",
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "pdf_version": "v1",
                "role": "user",
                "content": "Can you explain what a JOIN is?",
                "mode": "tutor"
            }
        }


class ChatRequest(BaseModel):
    """Chat request from user"""
    job_id: str
    pdf_version: str
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "job_id": "550e8400-e29b-41d4-a716-446655440000",
                "pdf_version": "v1",
                "message": "Can you explain what a JOIN is?"
            }
        }


class ChatResponse(BaseModel):
    """Chat response to user"""
    message_id: str
    content: str
    mode: ChatMode
    citations: Optional[List[str]] = None
    new_pdf_version: Optional[str] = None  # Set if edit was applied
    timestamp: datetime = Field(default_factory=datetime.utcnow)
