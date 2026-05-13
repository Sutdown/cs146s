"""
Notes router with well-defined API contracts.
"""
from fastapi import APIRouter, HTTPException, status

from .. import db
from ..schemas import NoteCreate, NoteResponse

router = APIRouter(prefix="/notes", tags=["notes"])


@router.post(
    "",
    response_model=NoteResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new note",
    description="Creates a new note with the provided content."
)
def create_note(payload: NoteCreate) -> NoteResponse:
    """
    Create a new note.

    - **content**: The content of the note (required)
    """
    try:
        note_id = db.insert_note(payload.content)
        note = db.get_note(note_id)
        
        if note is None:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to retrieve created note"
            )
        
        return NoteResponse(**note)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create note: {str(e)}"
        )


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get a note by ID",
    description="Retrieves a specific note by its ID."
)
def get_single_note(note_id: int) -> NoteResponse:
    """
    Get a note by its ID.

    - **note_id**: The ID of the note to retrieve
    """
    note = db.get_note(note_id)
    
    if note is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id={note_id} not found"
        )
    
    return NoteResponse(**note)


@router.get(
    "",
    response_model=list[NoteResponse],
    summary="List all notes",
    description="Retrieves all notes, ordered by most recent first."
)
def list_all_notes() -> list[NoteResponse]:
    """
    List all notes in the database.
    """
    notes = db.list_notes()
    return [NoteResponse(**note) for note in notes]


@router.delete(
    "/{note_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a note",
    description="Deletes a specific note by its ID."
)
def delete_note(note_id: int) -> None:
    """
    Delete a note by its ID.

    - **note_id**: The ID of the note to delete
    """
    deleted = db.delete_note(note_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Note with id={note_id} not found"
        )
