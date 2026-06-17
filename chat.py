"""LangChain-based tutor chat logic with Ollama integration.

The tutor acts as a friendly teacher who:
- Explains concepts using simple, relatable analogies
- Asks a follow-up question after each explanation to check understanding
- Maintains a patient and encouraging tone
- Adapts explanations based on the student's level
"""

import json
import re
from typing import Any

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_ollama import ChatOllama

# ── Configuration ──────────────────────────────────────────────────────────

OLLAMA_BASE_URL = "http://154.57.212.236:11434"
OLLAMA_MODEL = "llama3.1:latest"
OLLAMA_TEMPERATURE = 0.7
OLLAMA_TOP_P = 0.9
OLLAMA_MAX_TOKENS = 1024

# ── System Prompt ─────────────────────────────────────────────────────────

TUTOR_SYSTEM_PROMPT = """You are TutorAI, a warm, friendly, and highly effective tutor. Your purpose is to help students learn any topic they ask about.

## Your Teaching Style

1. **Be Encouraging**: Start every response with warmth. Praise effort and curiosity.
2. **Use Analogies**: Explain every concept with at least one simple, everyday analogy that makes the abstract concrete.
3. **Keep It Simple**: Break down complex topics into bite-sized pieces. Avoid jargon unless you explain it right away.
4. **Check Understanding**: ALWAYS end your explanation with a follow-up question that tests whether the student understood the concept you just explained.
5. **Be Patient**: If a student seems confused, re-explain using a different analogy. Never make the student feel bad for not understanding.
6. **Be Concise**: Keep explanations focused. Aim for 3-5 paragraphs max per turn.

## Conversation Format

- The conversation history is provided below.
- Respond as the tutor in a natural, conversational tone.
- After your explanation, always ask ONE specific follow-up question.
- Never answer for the student or assume they understood — ask!

Remember: You are a friendly teacher, not a text book. Make learning fun and engaging!"""


# ── Helper: build LangChain messages from DB history ──────────────────────


def build_messages_from_history(
    history: list[dict[str, Any]],
    current_message: str,
) -> list:
    """Convert database chat history + current message into LangChain message objects."""
    messages: list = [SystemMessage(content=TUTOR_SYSTEM_PROMPT)]

    for msg in history:
        if msg["role"] == "user":
            messages.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            messages.append(AIMessage(content=msg["content"]))

    messages.append(HumanMessage(content=current_message))
    return messages


# ── Get LLM instance ──────────────────────────────────────────────────────


def get_llm() -> ChatOllama:
    """Get a configured ChatOllama instance."""
    return ChatOllama(
        model=OLLAMA_MODEL,
        base_url=OLLAMA_BASE_URL,
        temperature=OLLAMA_TEMPERATURE,
        top_p=OLLAMA_TOP_P,
        num_predict=OLLAMA_MAX_TOKENS,
    )


# ── Generate tutor response ────────────────────────────────────────────────


def generate_tutor_response(
    history: list[dict[str, Any]],
    current_message: str,
) -> str:
    """Generate a tutor response using LangChain + Ollama.

    Args:
        history: List of message dicts with 'role' and 'content' keys.
        current_message: The student's latest message.

    Returns:
        The tutor's response text.
    """
    llm = get_llm()
    messages = build_messages_from_history(history, current_message)
    response = llm.invoke(messages)
    return response.content


# ── Smart Endpoint Helpers (LLM-based analysis) ──────────────────────────


TOPIC_EXTRACTION_PROMPT = """You are an AI teaching assistant analyzing a student's tutoring conversation history.

Based on the following conversation history, identify ALL academic topics the student has studied or asked about.

For each topic, provide:
1. The topic name (be specific, e.g. "Newton's Laws of Motion" not just "Physics")
2. The student's apparent confidence level: Beginning, Developing, or Proficient
3. A brief note on when it was discussed

Return your answer as a JSON list of objects with keys: "topic", "confidence", "last_mentioned".

Conversation history:
{history}

Return ONLY valid JSON, no other text."""

WEAK_AREAS_PROMPT = """You are an AI teaching assistant analyzing a student's tutoring conversation history.

Based on the following conversation history, identify topics the student seems to be STRUGGLING with or confused about.
Look for signs like:
- The student asked for re-explanation
- The student gave incorrect answers to follow-up questions
- The student expressed confusion
- The tutor had to explain the same concept multiple times

For each weak area, provide:
1. The topic name
2. Difficulty level: Low, Medium, or High
3. Evidence from the conversation that shows this is a weak area

Return your answer as a JSON list of objects with keys: "topic", "difficulty", "evidence".

Conversation history:
{history}

Return ONLY valid JSON, no other text."""

STUDY_PLAN_PROMPT = """You are an AI teaching assistant creating a personalized study plan for a student.

The student has been identified as struggling with the following topics:
{weak_areas}

The student's conversation history:
{history}

Create a {days}-day study plan with approximately {hours_per_day} hours of study per day.
For each day, specify:
1. Which topic to study
2. How many minutes to spend (based on {hours_per_day} hours/day)
3. Specific activities (e.g., "Review the concept of X", "Practice problem Y", "Watch a video on Z")
4. Any resources or practice suggestions

Return your answer as a JSON object with key "plan", which is a list of objects with keys:
"day" (integer), "topic" (string), "duration_minutes" (integer), "activities" (list of strings), "resources" (list of strings).

Return ONLY valid JSON, no other text."""


def extract_topics(history: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Extract topics the student has studied from chat history using LLM."""
    if not history:
        return []

    history_text = _format_history_for_prompt(history)
    llm = get_llm()
    prompt = TOPIC_EXTRACTION_PROMPT.format(history=history_text)
    response = llm.invoke([SystemMessage(content="You are a helpful teaching assistant."), HumanMessage(content=prompt)])
    return _parse_json_response(response.content)


def extract_weak_areas(history: list[dict[str, Any]]) -> list[dict[str, str]]:
    """Detect topics the student is struggling with using LLM."""
    if not history:
        return []

    history_text = _format_history_for_prompt(history)

    # Build a more targeted prompt: focus on struggles
    llm = get_llm()
    prompt = WEAK_AREAS_PROMPT.format(history=history_text)
    response = llm.invoke([SystemMessage(content="You are a helpful teaching assistant."), HumanMessage(content=prompt)])
    return _parse_json_response(response.content)


def generate_study_plan(
    weak_areas: list[dict[str, str]],
    history: list[dict[str, Any]],
    days: int = 7,
    hours_per_day: float = 1.0,
) -> list[dict[str, Any]]:
    """Generate a personalized study plan based on weak areas."""
    if not weak_areas:
        return []

    history_text = _format_history_for_prompt(history)
    weak_areas_text = json.dumps([w["topic"] for w in weak_areas], indent=2)

    llm = get_llm()
    prompt = STUDY_PLAN_PROMPT.format(
        weak_areas=weak_areas_text,
        history=history_text,
        days=days,
        hours_per_day=hours_per_day,
    )
    response = llm.invoke([SystemMessage(content="You are a helpful teaching assistant."), HumanMessage(content=prompt)])

    parsed = _parse_json_response(response.content)
    if isinstance(parsed, dict) and "plan" in parsed:
        return parsed["plan"]
    return parsed if isinstance(parsed, list) else []


# ── Helpers ────────────────────────────────────────────────────────────────


def _format_history_for_prompt(history: list[dict[str, Any]]) -> str:
    """Format chat history into a readable text for LLM prompts."""
    lines = []
    for msg in history:
        role_label = "Student" if msg["role"] == "user" else "Tutor"
        lines.append(f"{role_label}: {msg['content']}")
    return "\n\n".join(lines)


def _parse_json_response(text: str) -> Any:
    """Try to parse JSON from LLM response, handling markdown code fences."""
    # Try to extract JSON from markdown code blocks
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if match:
        text = match.group(1).strip()

    # Try direct JSON parse
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find JSON array or object in the text
        array_match = re.search(r"\[.*\]", text, re.DOTALL)
        if array_match:
            try:
                return json.loads(array_match.group())
            except json.JSONDecodeError:
                pass
        obj_match = re.search(r"\{.*\}", text, re.DOTALL)
        if obj_match:
            try:
                return json.loads(obj_match.group())
            except json.JSONDecodeError:
                pass
        return []
