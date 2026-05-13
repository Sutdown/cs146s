from __future__ import annotations

import json
import logging
import re
from typing import List, Any

from ollama import chat
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

BULLET_PREFIX_PATTERN = re.compile(r"^\s*([-*•]|\d+\.)\s+")
KEYWORD_PREFIXES = (
    "todo:",
    "action:",
    "next:",
)


def _is_action_line(line: str) -> bool:
    stripped = line.strip().lower()
    if not stripped:
        return False
    if BULLET_PREFIX_PATTERN.match(stripped):
        return True
    if any(stripped.startswith(prefix) for prefix in KEYWORD_PREFIXES):
        return True
    if "[ ]" in stripped or "[todo]" in stripped:
        return True
    return False


def extract_action_items(text: str) -> List[str]:
    lines = text.splitlines()
    extracted: List[str] = []
    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            continue
        if _is_action_line(line):
            cleaned = BULLET_PREFIX_PATTERN.sub("", line)
            cleaned = cleaned.strip()
            # Trim common checkbox markers
            cleaned = cleaned.removeprefix("[ ]").strip()
            cleaned = cleaned.removeprefix("[todo]").strip()
            extracted.append(cleaned)
    # Fallback: if nothing matched, heuristically split into sentences and pick imperative-like ones
    if not extracted:
        sentences = re.split(r"(?<=[.!?])\s+", text.strip())
        for sentence in sentences:
            s = sentence.strip()
            if not s:
                continue
            if _looks_imperative(s):
                extracted.append(s)
    # Deduplicate while preserving order
    seen: set[str] = set()
    unique: List[str] = []
    for item in extracted:
        lowered = item.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        unique.append(item)
    return unique


def _looks_imperative(sentence: str) -> bool:
    words = re.findall(r"[A-Za-z']+", sentence)
    if not words:
        return False
    first = words[0]
    # Crude heuristic: treat these as imperative starters
    imperative_starters = {
        "add",
        "create",
        "implement",
        "fix",
        "update",
        "write",
        "check",
        "verify",
        "refactor",
        "document",
        "design",
        "investigate",
    }
    return first.lower() in imperative_starters


def extract_action_items_llm(text: str) -> List[str]:
    """
    Extract action items using LLM (Ollama).

    Args:
        text: Input text containing notes.

    Returns:
        List of extracted action item strings.
    """
    if not text.strip():
        return []

    prompt = f"""You are an action item extractor. Your task is to identify all actionable items (tasks, todos, things to do) from the text below and return them as a JSON array.

Each item should be a clear, concise task description without prefixes like "- ", "* ", "[ ]", "TODO:", etc.

Input text:
{text}

Return a JSON array of strings only. Example:
["week1", "week2", "week3", "week4"]

JSON array:"""

    try:
        response = chat(
            model="mistral-nemo:12b",
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            options={"temperature": 0.1},
        )

        raw_output = response.message.content or "[]"
        logger.info(f"LLM raw output: {raw_output}")  # Debug

        # Try to extract JSON from the response (handle markdown code blocks)
        json_str = raw_output.strip()
        
        # Remove markdown code blocks if present
        if json_str.startswith("```"):
            # Remove ```json or ``` at the start
            json_str = json_str.split("```")[1] if "```" in json_str else json_str
            # Remove language identifier if present (e.g., "json")
            json_str = json_str.lstrip("json\n").lstrip("json")
        
        # Try to parse the JSON
        result = json.loads(json_str)

        # Ensure result is a list
        if isinstance(result, dict) and "items" in result:
            items = result["items"]
        elif isinstance(result, list):
            items = result
        else:
            items = []

        # Clean up items - remove checkbox markers and prefixes
        cleaned_items: List[str] = []
        for item in items:
            if isinstance(item, str):
                cleaned = item.strip()
                # Remove common prefixes
                cleaned = re.sub(r"^[\-\*\•]+\s*", "", cleaned)
                cleaned = re.sub(r"^\[.\]\s*", "", cleaned)
                cleaned = re.sub(r"^todo\d*:\s*", "", cleaned, flags=re.IGNORECASE)
                cleaned = cleaned.strip()
                if cleaned:
                    cleaned_items.append(cleaned)

        # Deduplicate while preserving order
        seen: set[str] = set()
        unique: List[str] = []
        for item in cleaned_items:
            lowered = item.lower()
            if lowered and lowered not in seen:
                seen.add(lowered)
                unique.append(item)

        return unique

    except Exception as e:
        logger.error(f"LLM extraction failed: {e}")
        # Fallback to rule-based extraction
        return extract_action_items(text)
