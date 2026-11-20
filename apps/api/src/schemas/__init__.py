"""
Brainly API - Pydantic Schemas

Request/Response models for API validation.
"""
from .workspace import (
    WorkspaceCreate,
    WorkspaceUpdate,
    WorkspaceResponse,
    AgentConfigUpdate,
    AgentConfigResponse,
)
from .kb import (
    KBSourceCreate,
    KBSourceUpdate,
    KBSourceResponse,
    FAQEntryCreate,
    FAQBulkCreate,
)
from .chat import (
    ChatMessageRequest,
    ChatMessageResponse,
    ChatMessageStreamChunk,
    ConversationResponse,
    ConversationListResponse,
    EscalationRequest,
    LeadCaptureRequest,
)
from .lead import LeadResponse, LeadUpdate
from .analytics import AnalyticsOverviewResponse
from .faq import FAQSuggestionResponse, FAQSuggestionAction

__all__ = [
    # Workspace
    "WorkspaceCreate",
    "WorkspaceUpdate",
    "WorkspaceResponse",
    "AgentConfigUpdate",
    "AgentConfigResponse",
    # KB
    "KBSourceCreate",
    "KBSourceUpdate",
    "KBSourceResponse",
    "FAQEntryCreate",
    "FAQBulkCreate",
    # Chat
    "ChatMessageRequest",
    "ChatMessageResponse",
    "ChatMessageStreamChunk",
    "ConversationResponse",
    "ConversationListResponse",
    "EscalationRequest",
    "LeadCaptureRequest",
    # Lead
    "LeadResponse",
    "LeadUpdate",
    # Analytics
    "AnalyticsOverviewResponse",
    # FAQ
    "FAQSuggestionResponse",
    "FAQSuggestionAction",
]