from fastapi import APIRouter, HTTPException

from app.database import get_chat_history, get_student
from app.models import (
    ErrorResponse,
    StudyDay,
    StudyPlanRequest,
    StudyPlanResponse,
    TopicResponse,
    TopicsListResponse,
    WeakAreaResponse,
    WeakAreasResponse,
)
from app.services.ai_service import (
    extract_topics,
    extract_weak_areas,
    generate_study_plan,
)

router = APIRouter(prefix="/students", tags=["Smart Analysis"])


@router.get(
    "/{student_id}/topics",
    response_model=TopicsListResponse,
    summary="Extract all topics the student has studied",
    responses={
        404: {"model": ErrorResponse, "description": "Student not found"},
        503: {"model": ErrorResponse, "description": "Ollama server unavailable"},
    },
)
def get_student_topics(student_id: int):
    """Analyze chat history and extract all academic topics discussed."""
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")

    history = get_chat_history(student_id)
    if not history:
        raise HTTPException(status_code=400, detail="No chat history found. Chat with the tutor first!")

    try:
        topics = extract_topics(history)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to analyze topics. Error: {exc}")

    return TopicsListResponse(
        student_id=student_id,
        topics=[TopicResponse(**t) for t in topics],
    )


@router.get(
    "/{student_id}/weak-areas",
    response_model=WeakAreasResponse,
    summary="Detect topics the student is struggling with",
    responses={
        404: {"model": ErrorResponse, "description": "Student not found"},
        503: {"model": ErrorResponse, "description": "Ollama server unavailable"},
    },
)
def get_student_weak_areas(student_id: int):
    """Analyze chat history to find topics the student is struggling with."""
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")

    history = get_chat_history(student_id)
    if not history:
        raise HTTPException(status_code=400, detail="No chat history found. Chat with the tutor first!")

    try:
        weak_areas = extract_weak_areas(history)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to analyze weak areas. Error: {exc}")

    return WeakAreasResponse(
        student_id=student_id,
        weak_areas=[WeakAreaResponse(**w) for w in weak_areas],
    )


@router.post(
    "/{student_id}/study-plan",
    response_model=StudyPlanResponse,
    summary="Generate a personalized study plan",
    responses={
        404: {"model": ErrorResponse, "description": "Student not found"},
        503: {"model": ErrorResponse, "description": "Ollama server unavailable"},
    },
)
def generate_study_plan_endpoint(student_id: int, body: StudyPlanRequest = StudyPlanRequest()):
    """Generate a day-by-day study plan based on the student's weak areas."""
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")

    history = get_chat_history(student_id)
    if not history:
        raise HTTPException(status_code=400, detail="No chat history found. Chat with the tutor first!")

    try:
        weak_areas = extract_weak_areas(history)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to analyze weak areas. Error: {exc}")

    if not weak_areas:
        raise HTTPException(status_code=400, detail="No weak areas detected yet.")

    try:
        plan = generate_study_plan(weak_areas, history, body.days, body.hours_per_day)
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Failed to generate study plan. Error: {exc}")

    return StudyPlanResponse(
        student_id=student_id,
        student_name=student["name"],
        weak_areas=[w["topic"] for w in weak_areas],
        plan=[StudyDay(**d) for d in plan],
    )