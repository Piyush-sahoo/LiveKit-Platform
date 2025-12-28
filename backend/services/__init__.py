"""Services package - re-exports from microservice submodules."""

# Analytics services (calls, analysis, recordings)
from .analytics.call_service import CallService
from .analytics.analysis_service import AnalysisService
from .analytics.webhook_service import WebhookService
from .analytics.s3_service import S3Service

# Config services (assistants, phones, SIP, tools)
from .config.assistant_service import AssistantService
from .config.phone_sip_service import PhoneNumberService, SipConfigService
from .config.tool_service import ToolService

# Orchestration services (campaigns)
from .orchestration.campaign_service import CampaignService

__all__ = [
    # Analytics
    "CallService",
    "AnalysisService",
    "WebhookService",
    "S3Service",
    # Config
    "AssistantService",
    "PhoneNumberService",
    "SipConfigService",
    "ToolService",
    # Orchestration
    "CampaignService",
]
