#!/usr/bin/env python3
"""Formatting utilities for Hermes CLI (backward compatibility layer)."""

# Re-export from core for backward compatibility
from hermes_cli.core.formatting import (
    format_duration_compact,
    format_token_count_compact,
    strip_reasoning_tags,
)

__all__ = ["format_duration_compact", "format_token_count_compact", "strip_reasoning_tags"]
