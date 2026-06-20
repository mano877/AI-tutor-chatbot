"""Pydantic models for request/response schemas."""

from datetime import datetime

from pydantic import BaseModel, Field


# ── Student Schemas ───────────────────────────────────────────────────────


class StudentCreate(BaseModel):
    """Request body for registering a new student."""

    name: str = Field(..., min_length=1, max_length=255, description="Student's full name")
    email: str = Field(..., min_length=5, max_length=255, description="Student's email address")


class StudentResponse(BaseModel):
    """Response body for student data."""

    id: int
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StudentListResponse(BaseModel):
    """Wrapper for listing students."""

    students: list[StudentResponse]
    total: int


# ── Chat Schemas ──────────────────────────────────────────────────────────


class ChatRequest(BaseModel):
    """Request body for sending a chat message."""

    student_id: int = Field(..., description="ID of the student")
    message: str = Field(..., min_length=1, max_length=5000, description="The student's message")


class ChatMessageResponse(BaseModel):
    """A single chat message in responses."""

    id: int
    role: str
    content: str
    timestamp: datetime


class ChatResponse(BaseModel):
    """Response body after a chat interaction."""

    student_id: int
    user_message: ChatMessageResponse
    tutor_message: ChatMessageResponse


class ChatHistoryResponse(BaseModel):
    """Response body for chat history."""

    student_id: int
    messages: list[ChatMessageResponse]
    total: int


# ── Smart Endpoint Schemas ────────────────────────────────────────────────


class TopicResponse(BaseModel):
    """A topic the student has studied."""

    topic: str
    confidence: str = Field(description="e.g. Beginning, Developing, Proficient")
    last_mentioned: str = Field(description="Brief context of when it was discussed")


class TopicsListResponse(BaseModel):
    """Response body for extracted topics."""

    student_id: int
    topics: list[TopicResponse]


class WeakAreaResponse(BaseModel):
    """A topic the student is struggling with."""

    topic: str
    difficulty: str = Field(description="e.g. Low, Medium, High")
    evidence: str = Field(description="Why this is a weak area based on conversation")


class WeakAreasResponse(BaseModel):
    """Response body for weak areas."""

    student_id: int
    weak_areas: list[WeakAreaResponse]


class StudyPlanRequest(BaseModel):
    """Optional request body for study plan generation."""

    days: int = Field(default=7, ge=1, le=30, description="Number of days for the plan")
    hours_per_day: float = Field(default=1.0, ge=0.5, le=8.0, description="Hours per day")


class StudyDay(BaseModel):
    """A single day in the study plan."""

    day: int
    topic: str
    duration_minutes: int
    activities: list[str]
    resources: list[str] = []


class StudyPlanResponse(BaseModel):
    """Response body for the personalized study plan."""

    student_id: int
    student_name: str
    weak_areas: list[str]
    plan: list[StudyDay]


# ── Error Schema ──────────────────────────────────────────────────────────


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str
