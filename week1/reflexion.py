import os
import re
from typing import Callable, Any, cast
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 1

SYSTEM_PROMPT = """
You are a coding assistant. Output ONLY a single fenced Python code block that defines
the function is_valid_password(password: str) -> bool. No prose or comments.
Keep the implementation minimal.
"""

# TODO: Fill this in!
YOUR_REFLEXION_PROMPT = """You are a Python expert specializing in password validation.

Your task is to analyze a failed implementation and provide an improved version.

Password validation rules:
1. At least 8 characters long
2. Must contain at least one lowercase letter
3. Must contain at least one uppercase letter
4. Must contain at least one digit
5. Must contain at least one special character (!@#$%^&*()-_)
6. Must NOT contain any whitespace

When you receive the previous code and failure information:
1. Carefully analyze which test cases failed and why
2. Identify the logic errors in the previous implementation
3. Provide a corrected implementation that handles ALL test cases
4. Output ONLY a single fenced Python code block (```python)
5. The function must be named exactly: is_valid_password(password: str) -> bool
6. Do not include explanations, comments, or additional text outside the code block"""


# Ground-truth test suite used to evaluate generated code
SPECIALS = set("!@#$%^&*()-_")
TEST_CASES: list[tuple[str, bool]] = [
    ("Password1!", True),       # valid
    ("password1!", False),      # missing uppercase
    ("Password!", False),       # missing digit
    ("Password1", False),       # missing special
]


def extract_code_block(text: str | None) -> str:
    """Extract code block from text, handling None input."""
    if text is None:
        return ""
    m = re.findall(r"```python\n([\s\S]*?)```", text, flags=re.IGNORECASE)
    if m:
        return m[-1].strip()
    m = re.findall(r"```\n([\s\S]*?)```", text)
    if m:
        return m[-1].strip()
    return text.strip()


def load_function_from_code(code_str: str) -> Callable[[str], bool]:
    namespace: dict[str, Any] = {}
    exec(code_str, namespace)  # noqa: S102 (executing controlled code from model for exercise)
    func = namespace.get("is_valid_password")
    if not callable(func):
        raise ValueError("No callable is_valid_password found in generated code")
    return cast(Callable[[str], bool], func)


def evaluate_function(func: Callable[[str], bool]) -> tuple[bool, list[str]]:
    failures: list[str] = []
    for pw, expected in TEST_CASES:
        try:
            result = bool(func(pw))
        except Exception as exc:
            failures.append(f"Input: {pw} → raised exception: {exc}")
            continue

        if result != expected:
            # Compute diagnostic based on ground-truth rules
            reasons = []
            if len(pw) < 8:
                reasons.append("length < 8")
            if not any(c.islower() for c in pw):
                reasons.append("missing lowercase")
            if not any(c.isupper() for c in pw):
                reasons.append("missing uppercase")
            if not any(c.isdigit() for c in pw):
                reasons.append("missing digit")
            if not any(c in SPECIALS for c in pw):
                reasons.append("missing special")
            if any(c.isspace() for c in pw):
                reasons.append("has whitespace")

            failures.append(
                f"Input: {pw} → expected {expected}, got {result}. Failing checks: {', '.join(reasons) or 'unknown'}"
            )

    return (len(failures) == 0, failures)


def generate_initial_function(system_prompt: str) -> str:
    response = chat(
        model="mistral-nemo:12b",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Provide the implementation now."},
        ],
        options={"temperature": 0.2},
    )
    return extract_code_block(response.message.content)


def your_build_reflexion_context(prev_code: str, failures: list[str]) -> str:
    """TODO: Build the user message for the reflexion step using prev_code and failures.

    Return a string that will be sent as the user content alongside the reflexion system prompt.
    """
    # Format the failure information
    failures_text = "\n".join(f"  - {f}" for f in failures)
    
    # Build the context message with previous code and failure analysis
    context = f"""The previous implementation failed the following test cases:

Failed Tests:
{failures_text}

Previous Code:
```python
{prev_code}
```

Please analyze why the previous implementation failed and provide a corrected version that passes all test cases.
Make sure to handle all password validation rules correctly.

Output ONLY the improved Python code block.
"""
    return context


def apply_reflexion(
    reflexion_prompt: str,
    build_context: Callable[[str, list[str]], str],
    prev_code: str,
    failures: list[str],
) -> str:
    reflection_context = build_context(prev_code, failures)
    print(f"REFLECTION CONTEXT: {reflection_context}, {reflexion_prompt}")
    response = chat(
        model="mistral-nemo:12b",
        messages=[
            {"role": "system", "content": reflexion_prompt},
            {"role": "user", "content": reflection_context},
        ],
        options={"temperature": 0.2},
    )
    return extract_code_block(response.message.content)


def run_reflexion_flow(
    system_prompt: str,
    reflexion_prompt: str,
    build_context: Callable[[str, list[str]], str],
) -> bool:
    # 1) Generate initial function
    initial_code = generate_initial_function(system_prompt)
    print("Initial code:\n" + initial_code)
    func = load_function_from_code(initial_code)
    passed, failures = evaluate_function(func)
    if passed:
        print("SUCCESS (initial implementation passed all tests)")
        return True
    else:
        print(f"FAILURE (initial implementation failed some tests): {failures}")

    # 2) Single reflexion iteration
    improved_code = apply_reflexion(reflexion_prompt, build_context, initial_code, failures)
    print("\nImproved code:\n" + improved_code)
    improved_func = load_function_from_code(improved_code)
    passed2, failures2 = evaluate_function(improved_func)
    if passed2:
        print("SUCCESS")
        return True

    print("Tests still failing after reflexion:")
    for f in failures2:
        print("- " + f)
    return False


if __name__ == "__main__":
    _ = run_reflexion_flow(SYSTEM_PROMPT, YOUR_REFLEXION_PROMPT, your_build_reflexion_context)
