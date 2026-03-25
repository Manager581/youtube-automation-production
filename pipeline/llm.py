#!/usr/bin/env python3
"""
LLM abstraction layer for the pipeline.

Priority order:
  1. Claude Max (via claude CLI) — best quality, uses your subscription
  2. Ollama (local) — free fallback
  3. Heuristic — no LLM, pattern-matching only

If Claude hits a rate limit or token issue, pauses and notifies the user.

Usage:
    from pipeline.llm import query_llm, LLMError

    response = query_llm("Score this topic...", json_mode=True)
"""

import json
import os
import re
import subprocess
import sys
import time
from typing import Optional


class LLMError(Exception):
    """Raised when all LLM backends fail."""
    pass


class TokenLimitError(LLMError):
    """Raised when Claude Max runs out of tokens."""
    pass


def query_claude(prompt: str, model: str = "opus", timeout: int = 120) -> Optional[str]:
    """Query Claude via the claude CLI (uses Max subscription).

    Args:
        prompt: The prompt to send
        model: "opus", "sonnet", or "haiku"
        timeout: Max seconds to wait
    """
    try:
        result = subprocess.run(
            ["claude", "-p", prompt, "--model", model, "--output-format", "text"],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()

        stderr = result.stderr.lower()
        if "rate limit" in stderr or "token" in stderr or "quota" in stderr:
            raise TokenLimitError(
                f"\n{'='*50}\n"
                f"  ⚠ CLAUDE MAX TOKEN LIMIT REACHED\n"
                f"  Program paused. Please wait for your limit to reset.\n"
                f"  Press Enter to retry, or Ctrl+C to quit.\n"
                f"{'='*50}\n"
            )
        # Other error — return None to fall through to next backend
        return None
    except FileNotFoundError:
        return None
    except subprocess.TimeoutExpired:
        return None


def query_ollama(prompt: str, model: str = "qwen3:4b", timeout: int = 90) -> Optional[str]:
    """Query local Ollama as fallback."""
    try:
        result = subprocess.run(
            ["ollama", "run", model, "--nowordwrap"],
            input=prompt,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return None


def query_llm(prompt: str, json_mode: bool = False,
              claude_model: str = "opus",
              ollama_model: str = "qwen3:4b") -> str:
    """Query LLM with automatic fallback chain.

    Priority: Claude Max → Ollama → raise LLMError

    Args:
        prompt: The prompt to send
        json_mode: If True, adds JSON instruction and validates response
        claude_model: Claude model to use ("opus", "sonnet", "haiku")
        ollama_model: Ollama model fallback

    Returns:
        LLM response text

    Raises:
        TokenLimitError: If Claude Max hits token limits (pauses for user)
        LLMError: If all backends fail
    """
    if json_mode:
        prompt = prompt + "\n\nRespond with ONLY valid JSON. No markdown, no explanation."

    # 1. Try Claude Max
    try:
        response = query_claude(prompt, model=claude_model)
        if response:
            if json_mode:
                return _extract_json(response)
            return response
    except TokenLimitError:
        # Pause and let user decide
        print("\n⚠  Claude Max token limit reached.")
        try:
            input("Press Enter to retry with Ollama, or Ctrl+C to quit: ")
        except KeyboardInterrupt:
            sys.exit(1)

    # 2. Try Ollama
    response = query_ollama(prompt, model=ollama_model)
    if response:
        if json_mode:
            return _extract_json(response)
        return response

    # 3. All failed
    raise LLMError("No LLM backend available. Install Ollama or check Claude CLI.")


def query_llm_json(prompt: str, **kwargs) -> dict:
    """Query LLM and parse JSON response.

    Returns parsed dict. Raises LLMError on failure.
    """
    response = query_llm(prompt, json_mode=True, **kwargs)
    try:
        return json.loads(response)
    except json.JSONDecodeError:
        # Try to extract JSON from response
        match = re.search(r'\{[\s\S]*\}', response)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        raise LLMError(f"Failed to parse JSON from LLM response: {response[:200]}")


def _extract_json(text: str) -> str:
    """Extract JSON from potentially wrapped response."""
    # Remove markdown code blocks
    text = re.sub(r'```json\s*', '', text)
    text = re.sub(r'```\s*', '', text)

    # Try to find JSON object or array
    match = re.search(r'[\{\[][\s\S]*[\}\]]', text)
    if match:
        return match.group()
    return text.strip()


def check_backends() -> dict:
    """Check which LLM backends are available."""
    backends = {}

    # Check Claude CLI
    try:
        result = subprocess.run(
            ["claude", "--version"],
            capture_output=True, text=True, timeout=5,
        )
        backends["claude"] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        backends["claude"] = False

    # Check Ollama
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True, text=True, timeout=5,
        )
        backends["ollama"] = result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        backends["ollama"] = False

    return backends


if __name__ == "__main__":
    backends = check_backends()
    print("LLM Backend Status:")
    for name, available in backends.items():
        status = "✅ Available" if available else "❌ Not found"
        print(f"  {name}: {status}")

    if any(backends.values()):
        print("\nQuick test:")
        try:
            resp = query_llm("Say 'hello' and nothing else.", claude_model="sonnet")
            print(f"  Response: {resp}")
        except LLMError as e:
            print(f"  Error: {e}")
