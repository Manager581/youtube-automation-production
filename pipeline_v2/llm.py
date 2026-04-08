#!/usr/bin/env python3
"""
llm.py — LLM abstraction layer. Claude only (via Claude Code CLI).
No Ollama. No paid Anthropic API. Uses Claude Max subscription (free).

Usage:
    from pipeline_v2.llm import query_claude, query_claude_vision
    response = query_claude("Your prompt here")
    response = query_claude_vision("Describe this image", image_path)
"""

import subprocess
import json
import shutil
import sys
import os

# Find claude CLI binary — check PATH first, then known install locations
def _find_claude_binary():
    # Check PATH
    found = shutil.which("claude")
    if found:
        return found
    # Known install locations on macOS
    candidates = [
        os.path.expanduser("~/Library/Application Support/Claude/claude-code/2.1.92/claude.app/Contents/MacOS/claude"),
        os.path.expanduser("~/.vscode/extensions/anthropic.claude-code-2.1.96-darwin-arm64/resources/native-binary/claude"),
        os.path.expanduser("~/.vscode/extensions/anthropic.claude-code-2.1.94-darwin-arm64/resources/native-binary/claude"),
        os.path.expanduser("~/.vscode/extensions/anthropic.claude-code-2.1.92-darwin-arm64/resources/native-binary/claude"),
    ]
    for c in candidates:
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
    # Glob for any version
    import glob
    for pattern in [
        os.path.expanduser("~/Library/Application Support/Claude/claude-code/*/claude.app/Contents/MacOS/claude"),
        os.path.expanduser("~/.vscode/extensions/anthropic.claude-code-*-darwin-arm64/resources/native-binary/claude"),
    ]:
        matches = sorted(glob.glob(pattern), reverse=True)  # newest first
        if matches:
            return matches[0]
    return "claude"  # fallback — will error with clear message

CLAUDE_BIN = _find_claude_binary()


def query_claude(prompt, max_tokens=4096, timeout=300):
    """Query Claude via Claude Code CLI (free on Claude Max).
    
    Args:
        prompt: The text prompt
        max_tokens: Max response tokens
        timeout: Seconds before timeout
    
    Returns:
        str: Claude's response text
    """
    try:
        # Pipe prompt via stdin to avoid OS arg length limits
        print(f"  [LLM] Sending {len(prompt)} chars to Claude CLI (timeout={timeout}s)...", file=sys.stderr)
        result = subprocess.run(
            [CLAUDE_BIN, "-p", "-", "--output-format", "text"],
            capture_output=True, text=True, timeout=timeout,
            input=prompt
        )
        print(f"  [LLM] RC={result.returncode}, stdout={len(result.stdout)} chars, stderr={len(result.stderr)} chars", file=sys.stderr)

        if result.returncode == 0:
            if not result.stdout.strip():
                print(f"  [LLM] WARNING: RC=0 but stdout is empty!", file=sys.stderr)
                print(f"  [LLM] stderr: {result.stderr[:500]}", file=sys.stderr)
            return result.stdout.strip()
        else:
            print(f"Claude CLI error (rc={result.returncode}): {result.stderr[:500]}", file=sys.stderr)
            return ""
    except FileNotFoundError:
        print("ERROR: 'claude' CLI not found. Install Claude Code.", file=sys.stderr)
        return ""
    except subprocess.TimeoutExpired:
        print(f"Claude CLI timed out after {timeout}s", file=sys.stderr)
        return ""


def query_claude_json(prompt, timeout=120):
    """Query Claude and parse JSON response.
    
    Args:
        prompt: Prompt that asks for JSON output
        timeout: Seconds before timeout
    
    Returns:
        dict: Parsed JSON response, or empty dict on failure
    """
    try:
        result = subprocess.run(
            [CLAUDE_BIN, "-p", prompt, "--output-format", "json"],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode == 0:
            return json.loads(result.stdout)
        return {}
    except (json.JSONDecodeError, FileNotFoundError, subprocess.TimeoutExpired):
        return {}


def query_claude_vision(prompt, image_path, timeout=120):
    """Query Claude with an image for vision analysis.
    
    Args:
        prompt: Text prompt describing what to analyze
        image_path: Path to image file
        timeout: Seconds before timeout
    
    Returns:
        str: Claude's response
    """
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}", file=sys.stderr)
        return ""
    
    full_prompt = f"[Image: {image_path}]\n\n{prompt}"
    return query_claude(full_prompt, timeout=timeout)


if __name__ == "__main__":
    # Self-test
    response = query_claude("Say 'Claude LLM layer working' and nothing else.")
    if "working" in response.lower():
        print(f"✅ Claude CLI working: {response}")
    else:
        print(f"❌ Claude CLI failed: {response}")
