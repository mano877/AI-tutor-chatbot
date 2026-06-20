from fastapi import APIRouter, HTTPException
from psycopg2.errors import UniqueViolation

from app.database.database import create_student, delete_student, get_student, list_students
from app.database.models import ErrorResponse, StudentCreate, StudentListResponse, StudentResponse

router = APIRouter(prefix="/students", tags=["Students"])


@router.post(
    "",
    response_model=StudentResponse,
    status_code=201,
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


@router.get("", response_model=StudentListResponse, summary="List all registered students")
def list_all_students():
    """Get a list of all registered students."""
    students = list_students()
    return StudentListResponse(students=students, total=len(students))


@router.get(
    "/{student_id}",
    response_model=StudentResponse,
    summary="Get a student's profile",
    responses={404: {"model": ErrorResponse, "description": "Student not found"}},
)
def get_student_profile(student_id: int):
    """Get a student's profile by ID."""
    student = get_student(student_id)
    if not student:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")
    return student


@router.delete(
    "/{student_id}",
    status_code=204,
    summary="Delete a student and all their data",
    responses={404: {"model": ErrorResponse, "description": "Student not found"}},
)
def delete_student_and_data(student_id: int):
    """Delete a student and all their chat history."""
    deleted = delete_student(student_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Student with id {student_id} not found.")
    return None