#!/usr/bin/env python3
"""Linux-specific clipboard utilities for Hermes CLI."""

import subprocess
import shutil
from typing import Optional


def get_linux_clipboard_tool() -> Optional[str]:
    """Detect available clipboard tool on Linux."""
    tools = ["wl-paste", "xclip", "xsel"]
    for tool in tools:
        if shutil.which(tool):
            return tool
    return None


def copy_to_clipboard(text: str) -> bool:
    """Copy text to clipboard using available Linux tool."""
    tool = get_linux_clipboard_tool()
    if not tool:
        return False
    
    try:
        if tool == "wl-paste":
            wl_copy = shutil.which("wl-copy")
            if wl_copy:
                subprocess.run([wl_copy], input=text.encode(), check=True)
                return True
        elif tool == "xclip":
            subprocess.run(["xclip", "-selection", "clipboard"], input=text.encode(), check=True)
            return True
        elif tool == "xsel":
            subprocess.run(["xsel", "--clipboard", "--input"], input=text.encode(), check=True)
            return True
    except (subprocess.SubprocessError, OSError):
        pass
    return False


def paste_from_clipboard() -> Optional[str]:
    """Paste text from clipboard using available Linux tool."""
    tool = get_linux_clipboard_tool()
    if not tool:
        return None
    
    try:
        if tool == "wl-paste":
            result = subprocess.run(["wl-paste"], capture_output=True, text=True, check=True)
            return result.stdout
        elif tool == "xclip":
            result = subprocess.run(["xclip", "-selection", "clipboard", "-o"], capture_output=True, text=True, check=True)
            return result.stdout
        elif tool == "xsel":
            result = subprocess.run(["xsel", "--clipboard", "--output"], capture_output=True, text=True, check=True)
            return result.stdout
    except (subprocess.SubprocessError, OSError):
        pass
    return None
