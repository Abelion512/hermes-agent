"""Linux-specific utilities for Hermes CLI."""

from hermes_cli.linux.clipboard import get_linux_clipboard_tool, copy_to_clipboard, paste_from_clipboard

__all__ = ["get_linux_clipboard_tool", "copy_to_clipboard", "paste_from_clipboard"]
