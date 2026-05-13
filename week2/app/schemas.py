"""
Pydantic schemas for API request/response validation.
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ============================================================================
# Note Schemas
# ============================================================================

class NoteCreate(BaseModel):
    """Request schema for creating a note."""
    content: str = Field(..., min_length=1, description="Note content")


class NoteResponse(BaseModel):
    """Response schema for a note."""
    id: int
    content: str
    created_at: str

    class Config:
        from_attributes = True


# ============================================================================
# Action Item Schemas
# ============================================================================

class ExtractRequest(BaseModel):
    """Request schema for extracting action items."""
    text: str = Field(..., min_length=1, description="Input text to extract from")
    save_note: bool = Field(default=False, description="Whether to save as a note")


class ActionItemResponse(BaseModel):
    """Response schema for a single action item."""
    id: int
    text: str

    class Config:
        from_attributes = True


class ExtractResponse(BaseModel):
    """Response schema for extraction results."""
    note_id: Optional[int] = None
    items: List[ActionItemResponse]


class ActionItemDetail(BaseModel):
    """Detailed action item with status."""
    id: int
    note_id: Optional[int]
    text: str
    done: bool
    created_at: str

    class Config:
        from_attributes = True


class MarkDoneRequest(BaseModel):
    """Request schema for marking action item done."""
    done: bool = Field(default=True, description="Completion status")


class MarkDoneResponse(BaseModel):
    """Response schema for mark done action."""
    id: int
    done: bool
