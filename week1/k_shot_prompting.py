import os
from dotenv import load_dotenv
from ollama import chat

load_dotenv()

NUM_RUNS_TIMES = 5

# TODO: Fill this in!
YOUR_SYSTEM_PROMPT = """You are a character-level string reversal assistant.

INSTRUCTION: To reverse a word, you MUST follow these steps:
1. Write out the word with each character on a separate line, with its index (starting from 0)
2. Then output the characters in REVERSE order (from last index to index 0)
3. Combine them WITHOUT spaces

EXAMPLES:

Input: "abc"
Step 1: a(0) b(1) c(2)
Step 2: c(2) b(1) a(0)
Output: cba

Input: "hello"
Step 1: h(0) e(1) l(2) l(3) o(4)
Step 2: o(4) l(3) l(2) e(1) h(0)
Output: olleh

Input: "httpstatus"
Step 1 (index each character): h(0) t(1) t(2) p(3) s(4) t(5) a(6) t(7) u(8) s(9)
Step 2 (read from last to first): s(9) u(8) t(7) a(6) t(5) s(4) p(3) t(2) t(1) h(0)
Output: "sutatsptth"

REMEMBER: Only output the final reversed word. No other text.

"""

USER_PROMPT = """
Reverse the order of letters in the following word. Only output the reversed word, no other text:

httpstatus
"""


EXPECTED_OUTPUT = "sutatsptth"

def test_your_prompt(system_prompt: str) -> bool:
    """Run the prompt up to NUM_RUNS_TIMES and return True if any output matches EXPECTED_OUTPUT.

    Prints "SUCCESS" when a match is found.
    """
    for idx in range(NUM_RUNS_TIMES):
        print(f"Running test {idx + 1} of {NUM_RUNS_TIMES}")
        response = chat(
            model="mistral-nemo:12b",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": USER_PROMPT},
            ],
            options={"temperature": 0.5},
        )
        output_text = response.message.content.strip() if isinstance(response.message.content, str) else ""
        if output_text.strip() == EXPECTED_OUTPUT.strip():
            print("SUCCESS")
            return True
        else:
            print(f"Expected output: {EXPECTED_OUTPUT}")
            print(f"Actual output: {output_text}")
    return False

if __name__ == "__main__":
    test_your_prompt(YOUR_SYSTEM_PROMPT)