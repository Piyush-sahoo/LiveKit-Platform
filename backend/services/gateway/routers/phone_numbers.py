"""Phone Numbers API endpoints with multi-tenancy support."""
import logging
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, Depends

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models import CreatePhoneNumberRequest
from services import PhoneNumberService
from shared.auth.dependencies import get_current_user_optional
from shared.auth.models import User

logger = logging.getLogger("api.phone_numbers")
router = APIRouter()


@router.post("/phone-numbers")
async def add_phone_number(
    request: CreatePhoneNumberRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Add a new phone number."""
    if not request.number.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in E.164 format (e.g., +919148227303)"
        )
    
    try:
        workspace_id = user.workspace_id if user else None
        phone = await PhoneNumberService.add_phone_number(request, workspace_id=workspace_id)
        return {
            "phone_id": phone.phone_id,
            "number": phone.number,
            "message": "Phone number added successfully",
        }
    except Exception as e:
        logger.error(f"Failed to add phone number: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/phone-numbers")
async def list_phone_numbers(
    is_active: Optional[bool] = Query(None),
    user: Optional[User] = Depends(get_current_user_optional)
):
    """List all phone numbers for current workspace."""
    workspace_id = user.workspace_id if user else None
    phones = await PhoneNumberService.list_phone_numbers(workspace_id=workspace_id, is_active=is_active)
    return {
        "phone_numbers": [p.to_dict() for p in phones],
        "count": len(phones),
    }


@router.get("/phone-numbers/{phone_id}")
async def get_phone_number(
    phone_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific phone number."""
    workspace_id = user.workspace_id if user else None
    phone = await PhoneNumberService.get_phone_number(phone_id, workspace_id=workspace_id)
    if not phone:
        raise HTTPException(status_code=404, detail="Phone number not found")
    return phone.to_dict()


@router.delete("/phone-numbers/{phone_id}")
async def delete_phone_number(
    phone_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Delete a phone number."""
    workspace_id = user.workspace_id if user else None
    deleted = await PhoneNumberService.delete_phone_number(phone_id, workspace_id=workspace_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Phone number not found")
    return {"message": "Phone number deleted successfully"}
