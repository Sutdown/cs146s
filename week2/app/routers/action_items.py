"""
Action Items router with well-defined API contracts.
"""
import logging
from typing import Optional, List

from fastapi import APIRouter, status

from .. import db
from ..schemas import (
    ExtractRequest,
    ExtractResponse,
    ActionItemResponse,
    ActionItemDetail,
    MarkDoneRequest,
    MarkDoneResponse,
)
from ..services.extract import extract_action_items, extract_action_items_llm

# Configure logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/action-items", tags=["action-items"])


@router.post(
    "/extract",
    response_model=ExtractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract action items (rule-based)",
    description="Extracts action items from text using rule-based pattern matching."
)
def extract(
    payload: ExtractRequest,
) -> ExtractResponse:
    """
    Extract action items using rule-based pattern matching.

    - **text**: Input text to extract action items from (required)
    - **save_note**: Whether to save the input as a note (default: False)
    """
    logger.info("Extracting action items (rule-based)")

    note_id: Optional[int] = None
    if payload.save_note:
        note_id = db.insert_note(payload.text)

    items = extract_action_items(payload.text)
    ids = db.insert_action_items(items, note_id=note_id)

    return ExtractResponse(
        note_id=note_id,
        items=[ActionItemResponse(id=i, text=t) for i, t in zip(ids, items)]
    )


@router.post(
    "/extract-llm",
    response_model=ExtractResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Extract action items (LLM)",
    description="Extracts action items from text using LLM (Ollama)."
)
def extract_llm(
    payload: ExtractRequest,
) -> ExtractResponse:
    """
    Extract action items using LLM (Ollama).

    - **text**: Input text to extract action items from (required)
    - **save_note**: Whether to save the input as a note (default: False)

    Note: This endpoint requires Ollama to be running.
    """
    logger.info("Extracting action items (LLM)")

    note_id: Optional[int] = None
    if payload.save_note:
        note_id = db.insert_note(payload.text)

    items = extract_action_items_llm(payload.text)
    ids = db.insert_action_items(items, note_id=note_id)

    return ExtractResponse(
        note_id=note_id,
        items=[ActionItemResponse(id=i, text=t) for i, t in zip(ids, items)]
    )


@router.get(
    "",
    response_model=list[ActionItemDetail],
    summary="List all action items",
    description="Retrieves all action items, optionally filtered by note ID."
)
def list_all(note_id: Optional[int] = None) -> list[ActionItemDetail]:
    """
    List all action items, optionally filtered by note ID.

    - **note_id**: Optional filter by note ID
    """
    rows = db.list_action_items(note_id=note_id)
    return [ActionItemDetail(**row) for row in rows]


@router.post(
    "/{action_item_id}/done",
    response_model=MarkDoneResponse,
    summary="Mark action item as done",
    description="Marks a specific action item as done or not done."
)
def mark_done(
    action_item_id: int,
    payload: MarkDoneRequest,
) -> MarkDoneResponse:
    """
    Mark an action item as done or not done.

    - **action_item_id**: The ID of the action item
    - **done**: Completion status (default: True)
    """
    logger.info(f"Marking action item {action_item_id} as done={payload.done}")
    db.mark_action_item_done(action_item_id, payload.done)
    return MarkDoneResponse(id=action_item_id, done=payload.done)
