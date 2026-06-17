"""AI Tutor Chatbot — FastAPI Application.

A friendly AI tutor that explains concepts using analogies and checks understanding.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException

from chat import (
    extract_topics,
    extract_weak_areas,
    generate_study_plan,
    generate_tutor_response,
)
from psycopg2.errors import UniqueViolation

from database import (
    add_chat_message,
    clear_chat_history,
    close_pool,
    create_student,
    delete_student,
    get_chat_history,
    get_student,
    init_db,
    list_students,
)
from models import (
    ChatHistoryResponse,
    ChatMessageResponse,
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    StudentCreate,
    StudentListResponse,
    StudentResponse,
    StudyPlanRequest,
    StudyPlanResponse,
    StudyDay,
    TopicsListResponse,
    TopicResponse,
    WeakAreasResponse,
    WeakAreaResponse,
)


# ── Lifespan ───────────────────────────────────────────────────────────────


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB. Shutdown: close connections."""
    init_db()
    yield
    close_pool()


app = FastAPI(
    title="AI Tutor Chatbot",
    description=(
        "A friendly AI tutor API. Students can register, chat with the tutor "
        "(who explains concepts using analogies and checks understanding), "
        "review history, and get personalized study plans."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# ── Students Endpoints ────────────────────────────────────────────────────


@app.post(
    "/students",
    response_model=StudentResponse,
    status_code=201,
    tags=["Students"],
    summary="Register a new student",
    responses={409: {"model": ErrorResponse, "description": "Email already exists"}},
)
def register_student(body: StudentCreate):
    """Register a new student with name and email."""
    try:
        student = create_student(body.name, body.email)
    except UniqueViolation:
        raise HTTPException(status_code=409, detail=f"Student with email '{body.email}' already exists.")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Database error: {exc}")
    return student


@app.get(
    "/students",
    response_model=StudentListResponse,
    tags=["Students"],
    summary="List all registered students",
)
def list_all_students():
    """Get a list of all registered students."""
    students = list_students()
    return StudentListResponse(students=students, total=len(students))


@app.get(
    "/students/{student_id}",
    response_model=StudentResponse,
    tags=["Students"],
    summary="Get a student's profile",
    responses={404: {"model": ErrorResponse, "description": "Student not found"}},
)
def get_student_profile(student_id: int):
    """Get a student's profile by ID."""
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")
    return student


@app.delete(
    "/students/{student_id}",
    status_code=204,
    tags=["Students"],
    summary="Delete a student and all their data",
    responses={404: {"model": ErrorResponse, "description": "Student not found"}},
)
def delete_student_and_data(student_id: int):
    """Delete a student and all their chat history."""
    deleted = delete_student(student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")
    return None


# ── Chat Endpoint ──────────────────────────────────────────────────────────


@app.post(
    "/chat",
    response_model=ChatResponse,
    tags=["Chat"],
    summary="Send a message to the tutor",
    responses={
        404: {"model": ErrorResponse, "description": "Student not found"},
        503: {"model": ErrorResponse, "description": "Ollama server unavailable"},
    },
)
def chat_with_tutor(body: ChatRequest):
    """Send a message to the AI tutor and get a response.

    The tutor loads the student's full chat history as context, responds
    with an analogy-driven explanation, and asks a follow-up question.
    """
    # Verify student exists
    student = get_student(body.student_id)
    if not student:
        raise HTTPException(
            status_code=404,
            detail=f"Student with id {body.student_id} not found.",
        )

    # Load history
    history = get_chat_history(body.student_id)

    # Save user message
    user_msg = add_chat_message(body.student_id, "user", body.message)

    # Generate tutor response
    try:
        tutor_text = generate_tutor_response(history, body.message)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to get response from AI tutor. Is the Ollama server running at http://154.57.212.236:11434? Error: {exc}",
        )

    # Save tutor response
    tutor_msg = add_chat_message(body.student_id, "assistant", tutor_text)

    return ChatResponse(
        student_id=body.student_id,
        user_message=ChatMessageResponse(**user_msg),
        tutor_message=ChatMessageResponse(**tutor_msg),
    )


# ── History Endpoints ─────────────────────────────────────────────────────


@app.get(
    "/students/{student_id}/history",
    response_model=ChatHistoryResponse,
    tags=["History"],
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


@app.delete(
    "/students/{student_id}/history",
    status_code=204,
    tags=["History"],
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


# ── Smart Endpoints ────────────────────────────────────────────────────────


@app.get(
    "/students/{student_id}/topics",
    response_model=TopicsListResponse,
    tags=["Smart Analysis"],
    summary="Extract all topics the student has studied",
    responses={
        404: {"model": ErrorResponse, "description": "Student not found"},
        503: {"model": ErrorResponse, "description": "Ollama server unavailable"},
    },
)
def get_student_topics(student_id: int):
    """Analyze the chat history and extract all academic topics discussed."""
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")

    history = get_chat_history(student_id)
    if not history:
        raise HTTPException(status_code=400, detail="No chat history found for this student. Chat with the tutor first!")

    try:
        topics = extract_topics(history)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to analyze topics. Is the Ollama server running? Error: {exc}",
        )

    return TopicsListResponse(
        student_id=student_id,
        topics=[TopicResponse(**t) for t in topics],
    )


@app.get(
    "/students/{student_id}/weak-areas",
    response_model=WeakAreasResponse,
    tags=["Smart Analysis"],
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
        raise HTTPException(status_code=400, detail="No chat history found for this student. Chat with the tutor first!")

    try:
        weak_areas = extract_weak_areas(history)
    except Exception as exc:
        print(f"FULL ERROR: {exc}")  # add this line
        raise HTTPException(
            status_code=503,
            detail=f"Failed to analyze weak areas. Is the Ollama server running? Error: {exc}",
        )

    return WeakAreasResponse(
        student_id=student_id,
        weak_areas=[WeakAreaResponse(**w) for w in weak_areas],
    )


@app.post(
    "/students/{student_id}/study-plan",
    response_model=StudyPlanResponse,
    tags=["Smart Analysis"],
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
        raise HTTPException(status_code=400, detail="No chat history found for this student. Chat with the tutor first!")

    try:
        weak_areas = extract_weak_areas(history)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to analyze weak areas. Is the Ollama server running? Error: {exc}",
        )

    if not weak_areas:
        raise HTTPException(
            status_code=400,
            detail="No weak areas detected! Either the student hasn't struggled with any topics yet, or there's not enough conversation history.",
        )

    try:
        plan = generate_study_plan(weak_areas, history, body.days, body.hours_per_day)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail=f"Failed to generate study plan. Is the Ollama server running? Error: {exc}",
        )

    return StudyPlanResponse(
        student_id=student_id,
        student_name=student["name"],
        weak_areas=[w["topic"] for w in weak_areas],
        plan=[StudyDay(**d) for d in plan],
    )


# ── Health Check ──────────────────────────────────────────────────────────


@app.get("/health", tags=["Health"], summary="Health check endpoint")
def health_check():
    """Check if the API is running."""
    return {"status": "healthy", "service": "AI Tutor Chatbot"}
