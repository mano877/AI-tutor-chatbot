from fastapi import APIRouter, HTTPException

from app.database.database import add_chat_message, clear_chat_history, get_chat_history, get_student
from app.database.models import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
)
from app.services.ai_service import generate_tutor_response

router = APIRouter(tags=["Chat & History"])


# ── Chat ──────────────────────────────────────

@router.post(
    "/chat",
    response_model=ChatResponse,
    summary="Send a message to the tutor",
    responses={
        404: {"model": ErrorResponse, "description": "Student not found"},
        503: {"model": ErrorResponse, "description": "Ollama server unavailable"},
    },
)
def chat_with_tutor(body: ChatRequest):
    """Send a message to the AI tutor and get a response."""
    student = get_student(body.student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {body.student_id} not found.")

    history = get_chat_history(body.student_id)
    user_msg = add_chat_message(body.student_id, "user", body.message)

    try:
        tutor_text = generate_tutor_response(history, body.message)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to get response from AI tutor. Error: {exc}")

    tutor_msg = add_chat_message(body.student_id, "assistant", tutor_text)

    return ChatResponse(
        student_id=body.student_id,
        user_message=ChatMessageResponse(**user_msg),
        tutor_message=ChatMessageResponse(**tutor_msg),
    )


# ── History ───────────────────────────────────

@router.get(
    "/students/{student_id}/history",
    response_model=ChatHistoryResponse,
    summary="Get a student's full conversation history",
    responses={404: {"model": ErrorResponse, "description": "Student not found"}},
)
def get_conversation_history(student_id: int):
    """Get the full chat conversation for a student."""
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")

    messages = get_chat_history(student_id)
    return ChatHistoryResponse(
        student_id=student_id,
        messages=[ChatMessageResponse(**m) for m in messages],
        total=len(messages),
    )


@router.delete(
    "/students/{student_id}/history",
    status_code=204,
    summary="Clear a student's conversation history",
    responses={404: {"model": ErrorResponse, "description": "Student not found"}},
)
def clear_conversation_history(student_id: int):
    """Delete all chat messages for a student."""
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")
    clear_chat_history(student_id)
    return None