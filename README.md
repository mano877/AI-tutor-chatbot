<div align="center">

# 🧑‍🏫 AI Tutor Chatbot API

**A friendly, analogy-driven AI tutor powered by FastAPI, LangChain, Ollama, and PostgreSQL**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.137+-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![LangChain](https://img.shields.io/badge/LangChain-1.3+-1C3C3C?logo=langchain&logoColor=white)](https://www.langchain.com)
[![Ollama](https://img.shields.io/badge/Ollama-llama3.1-000000?logo=ollama&logoColor=white)](https://ollama.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16+-4169E1?logo=postgresql&logoColor=white)](https://www.postgresql.org)
[![Python](https://img.shields.io/badge/Python-3.14+-3776AB?logo=python&logoColor=white)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![uv](https://img.shields.io/badge/uv-package%20manager-2B5C8F?logo=python&logoColor=white)](https://docs.astral.sh/uv)

</div>

---

## 📖 Overview

The **AI Tutor Chatbot API** is a RESTful backend that lets students learn any topic through natural conversation with an AI tutor. The tutor isn't just a Q&A bot — it's designed to **teach** using:

- 🧩 **Simple, relatable analogies** that make abstract concepts concrete
- ❓ **Follow-up questions** after every explanation to check understanding
- 🧠 **Smart analysis** that detects which topics a student has studied and where they're struggling
- 📅 **Personalized study plans** generated from conversation history

Built on **LangChain + Ollama (llama3.1:latest)** for the LLM layer and **PostgreSQL** for persistent storage, this API is production-ready and easy to deploy.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.14+
- [uv](https://docs.astral.sh/uv/) (fast Python package manager)
- [Ollama](https://ollama.com) running with `llama3.1:latest`
- PostgreSQL 16+

### 1️⃣ Clone & Install

```bash
# Clone the repository
git clone <repo-url>
cd tutor-chatbot

# Create a virtual environment and install dependencies with uv
uv sync
```

### 2️⃣ Configure Environment Variables

| Variable | Default | Description |
|---|---|---|
| `DB_HOST` | `localhost` | PostgreSQL host |
| `DB_PORT` | `portnumber` | PostgreSQL port |
| `DB_NAME` | `tutor_chatbot` | Database name |
| `DB_USER` | `username` | Database user |
| `DB_PASSWORD` | `yourpassword` | Database password |
| `DB_MIN_CONN` | `2` | Min pool connections |
| `DB_MAX_CONN` | `10` | Max pool connections |

### 3️⃣ Set Up the Database

```bash
# Create the database (adjust for your PostgreSQL setup)
createdb tutor_chatbot
```

The database tables are created automatically on first startup via `init_db()`.

### 4️⃣ Ensure Ollama is Running

```bash
# Start Ollama (if not already running)
ollama serve

# Pull the model
ollama pull llama3.1:latest
```

The API connects to Ollama at the URL configured in `chat.py`.

### 5️⃣ Start the API

```bash
uv run tutor-chatbot
# or
uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Visit **http://localhost:8000/docs** for the interactive Swagger UI.

---

## 🧭 API Endpoints

### 🧑‍🎓 Students

| Method | Path | Description |
|---|---|---|
| `POST` | `/students` | Register a new student |
| `GET` | `/students` | List all students |
| `GET` | `/students/{student_id}` | Get a student's profile |
| `DELETE` | `/students/{student_id}` | Delete a student and all their data |

**Register a student:**

```json
// POST /students
{
  "name": "Alice Johnson",
  "email": "alice@example.com"
}

// Response 201
{
  "id": 1,
  "name": "Alice Johnson",
  "email": "alice@example.com",
  "created_at": "2026-06-17T10:30:00Z"
}
```

### 💬 Chat

| Method | Path | Description |
|---|---|---|
| `POST` | `/chat` | Send a message to the tutor |

**Send a message:**

```json
// POST /chat
{
  "student_id": 1,
  "message": "Can you explain how gravity works?"
}

// Response 200
{
  "student_id": 1,
  "user_message": {
    "id": 5,
    "role": "user",
    "content": "Can you explain how gravity works?",
    "timestamp": "2026-06-17T10:31:00Z"
  },
  "tutor_message": {
    "id": 6,
    "role": "assistant",
    "content": "Great question! Think of gravity like a giant magnet...",
    "timestamp": "2026-06-17T10:31:05Z"
  }
}
```

### 📜 History

| Method | Path | Description |
|---|---|---|
| `GET` | `/students/{student_id}/history` | Get full conversation history |
| `DELETE` | `/students/{student_id}/history` | Clear conversation history |

### 🔍 Smart Analysis

| Method | Path | Description |
|---|---|---|
| `GET` | `/students/{student_id}/topics` | Extract all topics the student has studied |
| `GET` | `/students/{student_id}/weak-areas` | Detect topics the student is struggling with |
| `POST` | `/students/{student_id}/study-plan` | Generate a personalized study plan |

**Get topics studied:**

```json
// GET /students/1/topics

// Response 200
{
  "student_id": 1,
  "topics": [
    {
      "topic": "Gravity",
      "confidence": "Beginning",
      "last_mentioned": "Student asked for an explanation of gravity"
    },
    {
      "topic": "Newton's Laws of Motion",
      "confidence": "Developing",
      "last_mentioned": "Student discussed examples of inertia"
    }
  ]
}
```

**Get weak areas:**

```json
// GET /students/1/weak-areas

// Response 200
{
  "student_id": 1,
  "weak_areas": [
    {
      "topic": "Gravitational Potential Energy",
      "difficulty": "High",
      "evidence": "Student confused potential energy with kinetic energy when asked a follow-up question"
    }
  ]
}
```

**Generate a study plan:**

```json
// POST /students/1/study-plan
{
  "days": 5,
  "hours_per_day": 1.5
}

// Response 200
{
  "student_id": 1,
  "student_name": "Alice Johnson",
  "weak_areas": ["Gravitational Potential Energy", "Electromagnetic Forces"],
  "plan": [
    {
      "day": 1,
      "topic": "Gravitational Potential Energy",
      "duration_minutes": 90,
      "activities": [
        "Review the concept of gravitational potential energy",
        "Work through 3 practice problems about dropping objects from height"
      ],
      "resources": [
        "Khan Academy: Gravitational Potential Energy",
        "Practice worksheet on potential vs kinetic energy"
      ]
    },
    {
      "day": 2,
      "topic": "Gravitational Potential Energy",
      "duration_minutes": 90,
      "activities": [
        "Deep dive: derivation of PE = mgh",
        "Real-world application problems"
      ],
      "resources": [
        "Physics classroom interactive simulation"
      ]
    }
  ]
}
```

### ❤️ Health

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |

---

## 💡 Example Usage Flow

```bash
# 1. Register a student
curl -X POST http://localhost:8000/students \
  -H "Content-Type: application/json" \
  -d '{"name": "Bob Smith", "email": "bob@example.com"}'

# 2. Start chatting!
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"student_id": 1, "message": "What is a black hole?"}'

# 3. View conversation history
curl http://localhost:8000/students/1/history

# 4. Analyze topics covered
curl http://localhost:8000/students/1/topics

# 5. Find weak areas
curl http://localhost:8000/students/1/weak-areas

# 6. Get a personalized study plan
curl -X POST http://localhost:8000/students/1/study-plan \
  -H "Content-Type: application/json" \
  -d '{"days": 7, "hours_per_day": 1.0}'

# 7. Clear history and start fresh
curl -X DELETE http://localhost:8000/students/1/history
```

---

## 🗄️ Database Schema

### `students` Table

| Column | Type | Constraints |
|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` |
| `name` | `VARCHAR(255)` | `NOT NULL` |
| `email` | `VARCHAR(255)` | `UNIQUE NOT NULL` |
| `created_at` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` |

### `chat_messages` Table

| Column | Type | Constraints |
|---|---|---|
| `id` | `SERIAL` | `PRIMARY KEY` |
| `student_id` | `INTEGER` | `NOT NULL REFERENCES students(id) ON DELETE CASCADE` |
| `role` | `VARCHAR(50)` | `NOT NULL` — `'user'` or `'assistant'` |
| `content` | `TEXT` | `NOT NULL` |
| `timestamp` | `TIMESTAMP` | `DEFAULT CURRENT_TIMESTAMP` |

**Indexes:**

- `idx_chat_messages_student_id` on `chat_messages(student_id)`
- `idx_chat_messages_timestamp` on `chat_messages(student_id, timestamp)`

> Deleting a student (`DELETE FROM students WHERE id = ?`) automatically cascades to delete all their chat messages.

---

## 🏗️ Project Structure

```
tutor-chatbot/
├── main.py          # FastAPI app — routes, lifespan, and error handling
├── models.py        # Pydantic schemas for all request/response bodies
├── database.py      # PostgreSQL connection pool, CRUD operations
├── chat.py          # LangChain + Ollama integration, tutoring logic
├── pyproject.toml   # Project metadata and dependencies
└── README.md        # This file
```

---

## 🧪 Tech Stack

| Layer | Technology |
|---|---|
| **Framework** | [FastAPI](https://fastapi.tiangolo.com) with automatic OpenAPI docs |
| **LLM Orchestration** | [LangChain](https://www.langchain.com) with `langchain-ollama` |
| **AI Model** | [Ollama](https://ollama.com) — `llama3.1:latest` |
| **Database** | PostgreSQL 16+ with `psycopg2` connection pooling |
| **Validation** | [Pydantic](https://docs.pydantic.dev) v2 |
| **Package Manager** | [uv](https://docs.astral.sh/uv) |

---

## ⚙️ Configuration

Key settings in `chat.py`:

| Setting | Value |
|---|---|
| Ollama Base URL | `paste URL here` |
| Model | `llama3.1:latest` |
| Temperature | `0.7` |
| Top-P | `0.9` |
| Max Tokens | `1024` |

---

## 🤝 Contributing

Contributions are welcome! Feel free to open issues or submit pull requests.

---

## ⚠️ Disclaimer

> **This AI Tutor is an experimental educational tool.** While the tutor strives to provide accurate explanations using analogies and checking for understanding, the AI model (Llama 3.1 via Ollama) may occasionally produce **incorrect, misleading, or hallucinated content**. Always verify critical information with authoritative sources. This tool is intended as a **supplementary learning aid** and should not replace formal education, professional instruction, or expert guidance. The developers assume no liability for any outcomes resulting from the use of this software.

---

<div align="center">

Made with ❤️ for lifelong learners everywhere

</div>
