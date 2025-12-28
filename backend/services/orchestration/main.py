"""
Orchestration Service - Campaign management and call dispatch.
Port: 8003
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Depends, Query, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List

from shared.settings import config
from shared.database.connection import connect_to_database, close_database_connection, get_database
from shared.database.models import (
    Campaign, CampaignStatus, 
    CreateCampaignRequest, UpdateCampaignRequest
)
from shared.auth.dependencies import get_current_user, get_current_user_optional
from shared.auth.models import User

from .campaign_service import CampaignService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("orchestration-service")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown events."""
    # Startup
    logger.info("Starting Orchestration Service...")
    await connect_to_database(config.MONGODB_URI, config.MONGODB_DB_NAME)
    logger.info("Orchestration Service ready on port 8003")
    
    yield
    
    # Shutdown
    logger.info("Shutting down Orchestration Service...")
    await close_database_connection()


app = FastAPI(
    title="Vobiz Orchestration Service",
    description="Campaign management and call dispatch",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Health check
@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "orchestration"}


# ============= CAMPAIGNS API =============

@app.post("/campaigns")
async def create_campaign(
    request: CreateCampaignRequest,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Create a new campaign."""
    workspace_id = user.workspace_id if user else None
    campaign = await CampaignService.create_campaign(request, workspace_id)
    return campaign.to_dict()


@app.get("/campaigns")
async def list_campaigns(
    status: Optional[str] = None,
    limit: int = Query(50, le=100),
    skip: int = 0,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """List all campaigns."""
    workspace_id = user.workspace_id if user else None
    campaigns = await CampaignService.list_campaigns(
        workspace_id=workspace_id,
        status=CampaignStatus(status) if status else None,
        limit=limit,
        skip=skip
    )
    return [c.to_dict() for c in campaigns]


@app.get("/campaigns/{campaign_id}")
async def get_campaign(
    campaign_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get a specific campaign."""
    workspace_id = user.workspace_id if user else None
    campaign = await CampaignService.get_campaign(campaign_id, workspace_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign.to_dict()


@app.get("/campaigns/{campaign_id}/stats")
async def get_campaign_stats(
    campaign_id: str,
    user: Optional[User] = Depends(get_current_user_optional)
):
    """Get campaign statistics."""
    stats = await CampaignService.get_campaign_stats(campaign_id)
    if not stats:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return stats


@app.post("/campaigns/{campaign_id}/start")
async def start_campaign(
    campaign_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(get_current_user)
):
    """Start a campaign."""
    campaign = await CampaignService.start_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=400, detail="Cannot start campaign")
    return {"status": "started", "campaign_id": campaign_id}


@app.post("/campaigns/{campaign_id}/pause")
async def pause_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user)
):
    """Pause a running campaign."""
    campaign = await CampaignService.pause_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=400, detail="Cannot pause campaign")
    return {"status": "paused", "campaign_id": campaign_id}


@app.post("/campaigns/{campaign_id}/cancel")
async def cancel_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user)
):
    """Cancel a campaign."""
    campaign = await CampaignService.cancel_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=400, detail="Cannot cancel campaign")
    return {"status": "cancelled", "campaign_id": campaign_id}


# ============= JOB QUEUE API =============

@app.post("/jobs/campaign/{campaign_id}")
async def queue_campaign(
    campaign_id: str,
    user: User = Depends(get_current_user)
):
    """Queue a campaign for execution via Celery."""
    from .tasks_queue.tasks import execute_campaign
    
    task = execute_campaign.delay(campaign_id)
    return {
        "status": "queued",
        "campaign_id": campaign_id,
        "task_id": task.id
    }


@app.get("/jobs/{task_id}")
async def get_job_status(
    task_id: str,
    user: User = Depends(get_current_user)
):
    """Get status of a queued job."""
    from .tasks_queue.celery_app import celery_app
    
    result = celery_app.AsyncResult(task_id)
    return {
        "task_id": task_id,
        "status": result.status,
        "result": result.result if result.ready() else None
    }
