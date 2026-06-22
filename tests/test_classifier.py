"""
Test the LLM intent classifier with 20 sample voice command phrases.

Run: python3 tests/test_classifier.py
Requires: GROQ_API_KEY in .env or environment
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent dir to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load .env
env_path = Path(__file__).parent.parent / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

import anthropic

# Import the classifier, speech corrections, and GroqClientBridge
from server import classify_intent, apply_speech_corrections, GroqClientBridge


# Test cases: (input_text, expected_action)
TEST_CASES = [
    # open_terminal
    ("open the terminal", "open_terminal"),
    ("open cloud code", "open_terminal"),
    ("launch Claude Code", "open_terminal"),
    ("open up the terminal for me", "open_terminal"),
    ("start clock code", "open_terminal"),

    # browse
    ("search for Python tutorials", "browse"),
    ("go to github.com", "browse"),
    ("pull up React documentation", "browse"),
    ("look up restaurants near me", "browse"),
    ("Google the weather in New York", "browse"),

    # build
    ("build me a landing page", "build"),
    ("create a snake game", "build"),
    ("make a todo app with React", "build"),
    ("build a REST API for my project", "build"),
    ("create a dashboard for analytics", "build"),

    # open_app
    ("open notepad", "open_app"),
    ("open spotify", "open_app"),
    ("launch vs code", "open_app"),
    ("start the calculator app", "open_app"),

    # write_notepad
    ("write hello world in notepad", "write_notepad"),
    ("write a shopping list in notepad", "write_notepad"),
    ("type shopping list to notepad", "write_notepad"),

    # media
    ("skip this song", "media"),
    ("play the music", "media"),
    ("pause the track", "media"),
    ("go back a track", "media"),
    ("stop the music", "media"),

    # chat
    ("how are you doing today", "chat"),
    ("what time is it", "chat"),
    ("tell me a joke", "chat"),
    ("good morning FRIDAY", "chat"),
    ("what's the weather like", "chat"),
]


async def run_tests():
    api_key = os.getenv("GROQ_API_KEY", "") or os.getenv("ANTHROPIC_API_KEY", "")
    if not api_key:
        print("ERROR: GROQ_API_KEY not set")
        sys.exit(1)

    if api_key.startswith("gsk_"):
        client = GroqClientBridge(api_key=api_key)
    else:
        client = anthropic.AsyncAnthropic(api_key=api_key)

    passed = 0
    failed = 0

    print(f"\nRunning {len(TEST_CASES)} classification tests...\n")
    print(f"{'Input':<45} {'Expected':<15} {'Got':<15} {'Status'}")
    print("-" * 85)

    for text, expected in TEST_CASES:
        # Apply speech corrections first (like the real flow)
        corrected = apply_speech_corrections(text)
        result = await classify_intent(corrected, client)
        actual = result["action"]

        if actual == expected:
            status = "PASS"
            passed += 1
        else:
            status = "FAIL"
            failed += 1

        print(f"{text:<45} {expected:<15} {actual:<15} {status}")
        # Sleep 2.1 seconds to avoid Groq rate limit of 30 RPM
        await asyncio.sleep(2.1)

    print(f"\n{'='*85}")
    print(f"Results: {passed}/{len(TEST_CASES)} passed, {failed} failed")

    if failed == 0:
        print("All tests passed!")
    else:
        print(f"WARNING: {failed} tests failed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_tests())
