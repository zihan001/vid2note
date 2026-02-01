"""Chat endpoints for tutor and editor modes"""

from fastapi import APIRouter, HTTPException
import logging

from app.models import ChatRequest, ChatResponse, ChatMode

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat with the AI tutor or request PDF edits
    
    Modes:
    - Tutor: Answers questions about PDF content (default)
    - Editor: Modifies PDF when user says "create update to pdf"
    
    Args:
        request: Chat message with job_id and pdf_version
        
    Returns:
        AI response, with new PDF version if edit was applied
    """
    # TODO: Check for explicit edit trigger phrase
    # TODO: If "create update to pdf" in message -> Editor mode
    # TODO: Otherwise -> Tutor mode
    # TODO: Query PDF content for relevant context
    # TODO: Call LLM with appropriate prompt
    # TODO: If editor mode, generate new PDF version
    
    message_lower = request.message.lower()
    is_edit_request = "create update to pdf" in message_lower
    
    mode = ChatMode.EDITOR if is_edit_request else ChatMode.TUTOR
    
    logger.info(f"Chat request in {mode} mode for job {request.job_id}")
    
    # Mock response
    import uuid
    return ChatResponse(
        message_id=str(uuid.uuid4()),
        content="This is a placeholder response. Integration pending.",
        mode=mode,
        citations=["Section 2.1", "Page 5"] if mode == ChatMode.TUTOR else None,
        new_pdf_version="v2" if mode == ChatMode.EDITOR else None
    )
