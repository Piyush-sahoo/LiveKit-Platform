"""Calls API endpoints with multi-tenancy support."""
import logging
from typing import Optional
from datetime import datetime, timezone, timedelta

from fastapi import APIRouter, HTTPException, Query, Depends

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from shared.database.models import CallStatus, CreateCallRequest, CallResponse
from shared.database.connection import get_database
from services import CallService, WebhookService
from services.analytics.s3_service import S3Service
from shared.auth.dependencies import get_current_user, get_current_user_optional
from shared.auth.models import User

logger = logging.getLogger("api.calls")
router = APIRouter()


def get_workspace_filter(user: Optional[User]) -> dict:
    """
    Build workspace filter for queries.
    Returns empty dict if no user (auth disabled).
    Includes backwards compatibility: matches workspace_id OR null (legacy data).
    """
    if user and user.workspace_id:
        # Match either user's workspace OR null (legacy data without workspace)
        return {"$or": [
            {"workspace_id": user.workspace_id},
            {"workspace_id": None},
            {"workspace_id": {"$exists": False}},
        ]}
    return {}


@router.post("/calls", response_model=CallResponse)
async def create_call(
    request: CreateCallRequest,
    user: Optional[User] = Depends(get_current_user_optional),
):
    """
    Trigger a new outbound call.
    
    - **phone_number**: Phone number to call (E.164 format)
    - **instructions**: Optional custom instructions for the AI
    - **webhook_url**: Optional URL for call event notifications
    - **metadata**: Optional custom metadata
    """
    if not request.phone_number.startswith("+"):
        raise HTTPException(
            status_code=400,
            detail="Phone number must be in E.164 format (e.g., +919148227303)"
        )
    
    try:
        workspace_id = user.workspace_id if user else None
        call = await CallService.create_call(request, workspace_id=workspace_id)
        
        if call.webhook_url:
            await WebhookService.send_initiated(call)
        
        logger.info(f"Call created: {call.call_id} (workspace: {workspace_id})")
        
        return CallResponse(
            call_id=call.call_id,
            status=call.status.value,
            room_name=call.room_name,
            message="Call initiated successfully",
        )
        
    except Exception as e:
        logger.error(f"Failed to create call: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/calls/{call_id}")
async def get_call(
    call_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get details of a specific call."""
    workspace_id = user.workspace_id if user else None
    call = await CallService.get_call(call_id, workspace_id=workspace_id)
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    data = call.to_dict()
    if data.get("recording_url"):
        data["recording_url"] = S3Service.generate_presigned_url(data["recording_url"])
        
    return data


@router.get("/calls")
async def list_calls(
    status: Optional[str] = Query(None),
    phone_number: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=100),
    skip: int = Query(0, ge=0),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """List calls with optional filters."""
    status_enum = None
    if status:
        try:
            status_enum = CallStatus(status)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status. Must be one of: {[s.value for s in CallStatus]}"
            )
    
    workspace_id = user.workspace_id if user else None
    calls = await CallService.list_calls(
        status=status_enum,
        phone_number=phone_number,
        limit=limit,
        skip=skip,
        workspace_id=workspace_id,
    )
    
    call_dicts = []
    for call in calls:
        data = call.to_dict()
        if data.get("recording_url"):
            data["recording_url"] = S3Service.generate_presigned_url(data["recording_url"])
        call_dicts.append(data)

    return {
        "calls": call_dicts,
        "count": len(calls),
        "limit": limit,
        "skip": skip,
    }


@router.get("/calls/{call_id}/analysis")
async def get_call_analysis(
    call_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get post-call analysis for a specific call."""
    workspace_id = user.workspace_id if user else None
    call = await CallService.get_call(call_id, workspace_id=workspace_id)
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if not call.analysis:
        raise HTTPException(status_code=404, detail="Analysis not available")
    
    return {
        "call_id": call_id,
        "analysis": call.analysis.model_dump() if hasattr(call.analysis, 'model_dump') else call.analysis,
    }


@router.post("/calls/{call_id}/analyze")
async def trigger_analysis(
    call_id: str,
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Manually trigger post-call analysis."""
    from services import AnalysisService
    
    workspace_id = user.workspace_id if user else None
    call = await CallService.get_call(call_id, workspace_id=workspace_id)
    
    if not call:
        raise HTTPException(status_code=404, detail="Call not found")
    
    if call.status != CallStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Can only analyze completed calls")
    
    analysis = await AnalysisService.analyze_call(call_id)
    
    if not analysis:
        raise HTTPException(status_code=500, detail="Analysis failed")
    
    return {
        "call_id": call_id,
        "analysis": analysis.model_dump(),
        "message": "Analysis completed",
    }


@router.get("/analytics/calls")
async def get_call_analytics(
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get aggregated call analytics for current workspace."""
    db = get_database()
    workspace_filter = get_workspace_filter(user)
    
    # Get total counts by status
    pipeline = [
        {"$match": workspace_filter} if workspace_filter else {"$match": {}},
        {"$group": {
            "_id": "$status",
            "count": {"$sum": 1},
            "total_duration": {"$sum": "$duration_seconds"},
        }}
    ]
    
    status_stats = {}
    async for doc in db.calls.aggregate(pipeline):
        status_stats[doc["_id"]] = {
            "count": doc["count"],
            "total_duration_seconds": doc["total_duration"],
        }
    
    # Get today's calls
    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_filter = {**workspace_filter, "created_at": {"$gte": today_start.isoformat()}}
    today_count = await db.calls.count_documents(today_filter)
    
    # Total calls
    total_calls = await db.calls.count_documents(workspace_filter if workspace_filter else {})
    
    # Sentiment distribution (from analyzed calls)
    sentiment_pipeline = [
        {"$match": {**workspace_filter, "analysis.sentiment": {"$exists": True}}},
        {"$group": {"_id": "$analysis.sentiment", "count": {"$sum": 1}}}
    ]
    
    sentiment_stats = {}
    async for doc in db.calls.aggregate(sentiment_pipeline):
        sentiment_stats[doc["_id"]] = doc["count"]
    
    return {
        "total_calls": total_calls,
        "today_calls": today_count,
        "by_status": status_stats,
        "by_sentiment": sentiment_stats,
    }


@router.get("/analytics/summary")
async def get_analytics_summary(
    days: int = Query(7, ge=1, le=90),
    user: Optional[User] = Depends(get_current_user_optional),
):
    """Get call summary for the last N days for current workspace."""
    db = get_database()
    workspace_filter = get_workspace_filter(user)
    
    start_date = datetime.now(timezone.utc) - timedelta(days=days)
    
    # Daily breakdown with workspace filter
    match_filter = {**workspace_filter, "created_at": {"$gte": start_date.isoformat()}}
    
    pipeline = [
        {"$match": match_filter},
        {"$addFields": {
            "date_str": {"$substr": ["$created_at", 0, 10]}
        }},
        {"$group": {
            "_id": "$date_str",
            "total": {"$sum": 1},
            "completed": {"$sum": {"$cond": [{"$eq": ["$status", "completed"]}, 1, 0]}},
            "answered": {"$sum": {"$cond": [{"$eq": ["$status", "answered"]}, 1, 0]}},
            "failed": {"$sum": {"$cond": [{"$eq": ["$status", "failed"]}, 1, 0]}},
        }},
        {"$sort": {"_id": 1}},
    ]
    
    daily_stats = []
    async for doc in db.calls.aggregate(pipeline):
        daily_stats.append({
            "date": doc["_id"],
            "total": doc["total"],
            "completed": doc["completed"],
            "answered": doc["answered"],
            "failed": doc["failed"],
        })
    
    return {
        "period_days": days,
        "daily_breakdown": daily_stats,
    }
