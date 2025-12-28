"""Assistants API endpoints with multi-tenancy support."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models import (
    CreateAssistantRequest,
    UpdateAssistantRequest,
    AssistantResponse,
)
from services import AssistantService
from shared.auth.dependencies import get_current_user_optional
from shared.auth.models import User

logger = logging.getLogger("api.assistants")
router = APIRouter()


@router.post("/assistants", response_model=AssistantResponse)
async def create_assistant(
    request: CreateAssistantRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """
    Create a new AI assistant.
    
    - **name**: Name of the assistant
    - **instructions**: System prompt for the AI
    - **first_message**: What the AI says when call connects
    - **voice**: Voice configuration (provider, voice_id)
    - **webhook_url**: URL for call event notifications
    """
    try:
        workspace_id = user.workspace_id if user else None
        assistant = await AssistantService.create_assistant(request, workspace_id=workspace_id)
        
        return AssistantResponse(
            assistant_id=assistant.assistant_id,
            name=assistant.name,
            message="Assistant created successfully",
        )
        
    except Exception as e:
        logger.error(f"Failed to create assistant: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/assistants")
async def list_assistants(
    is_active: Optional[bool] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """List all assistants for current workspace."""
    workspace_id = user.workspace_id if user else None
    assistants = await AssistantService.list_assistants(
        workspace_id=workspace_id,
        is_active=is_active,
        limit=limit,
        skip=skip,
    )
    
    return {
        "assistants": [a.to_dict() for a in assistants],
        "count": len(assistants),
    }


@router.get("/assistants/{assistant_id}")
async def get_assistant(
    assistant_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific assistant."""
    workspace_id = user.workspace_id if user else None
    assistant = await AssistantService.get_assistant(assistant_id, workspace_id=workspace_id)
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return assistant.to_dict()


@router.patch("/assistants/{assistant_id}")
async def update_assistant(
    assistant_id: str,
    request: UpdateAssistantRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Update an assistant."""
    workspace_id = user.workspace_id if user else None
    assistant = await AssistantService.update_assistant(assistant_id, request, workspace_id=workspace_id)
    
    if not assistant:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return AssistantResponse(
        assistant_id=assistant.assistant_id,
        name=assistant.name,
        message="Assistant updated successfully",
    )


@router.delete("/assistants/{assistant_id}")
async def delete_assistant(
    assistant_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete an assistant."""
    workspace_id = user.workspace_id if user else None
    deleted = await AssistantService.delete_assistant(assistant_id, workspace_id=workspace_id)
    
    if not deleted:
        raise HTTPException(status_code=404, detail="Assistant not found")
    
    return {"message": "Assistant deleted successfully"}
