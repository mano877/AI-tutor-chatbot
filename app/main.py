"""AI Tutor Chatbot — FastAPI Application."""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database.database import init_db, close_pool
from app.routers import students, chat, smart


# ── Lifespan ───────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup: initialize DB. Shutdown: close connections."""
    init_db()
    yield
    close_pool()


# ── App ────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="📚 AI Tutor Chatbot",
    description=(
        "A friendly AI tutor API. Students can register, chat with the tutor "
        "(who explains concepts using analogies and checks understanding), "
        "review history, and get personalized study plans."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routers ────────────────────────────────────────────────────────────────
app.include_router(students.router)
app.include_router(chat.router)
app.include_router(smart.router)


# ── Root ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
def root():
    return {
        "message": "📚 AI Tutor Chatbot API is running!",
        "tutor": "TutorAI — Your friendly AI teacher",
        "docs": "/docs"
    }


@app.get("/health", tags=["Health"], summary="Health check endpoint")
def health_check():
    return {"status": "healthy", "service": "AI Tutor Chatbot"}