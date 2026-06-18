"""display_aesthetics plugin — Enhances LLM output formatting.

Wires:
1. ``transform_llm_output`` hook — wraps Markdown tables in code blocks for neatness.
"""

from __future__ import annotations

import logging
import re
from typing import Any, List, Optional

# Import internal alignment engine
from agent.markdown_tables import realign_markdown_tables

logger = logging.getLogger(__name__)

# Pattern to detect potential Markdown table blocks (contiguous lines containing pipes)
TABLE_BLOCK_RE = re.compile(r"((?:\n|^)(?:[^\n]*\|[^\n]*\n?)+)", re.MULTILINE)

# Asa-Style Templates
TEMPLATES = {
    "summary": """
### 📋 Ringkasan: {title}
{items}
    """,
    "status_block": """
```status
{content}
```
    """,
    "table_block": """
```table
{content}
```
    """,
}


def to_box_table(text: str) -> str:
    """Converts a GFM pipe table into a beautiful Unicode Box-Drawing table."""
    from wcwidth import wcswidth

    from agent.markdown_tables import is_table_divider, split_table_row

    def _width(s: str) -> int:
        w = wcswidth(s)
        return w if w > 0 else len(s)  # Fallback if wcswidth fails

    lines = [l.strip() for l in text.strip().split("\n") if l.strip()]
    grid = []
    for line in lines:
        if is_table_divider(line):
            continue
        row = split_table_row(line)
        if any(c.strip() for c in row):
            grid.append(row)

    if not grid:
        return text

    num_cols = max(len(row) for row in grid)
    grid = [row + [""] * (num_cols - len(row)) for row in grid]

    col_widths = []
    for c in range(num_cols):
        max_w = max((_width(row[c]) for row in grid), default=0)
        col_widths.append(max(max_w, 1) + 2)

    def get_line(left, mid, cross, right):
        return left + cross.join(mid * w for w in col_widths) + right

    top = get_line("┌", "─", "┬", "┐")
    sep = get_line("├", "─", "┼", "┤")
    bot = get_line("└", "─", "┴", "┘")

    out = [top]
    for i, row in enumerate(grid):
        cells = []
        for c, val in enumerate(row):
            target_w = col_widths[c]
            actual_w = _width(val)
            padding = " " * (target_w - actual_w - 1)
            cells.append(f" {val}{padding}")
        out.append("│" + "│".join(cells) + "│")
        if i < len(grid) - 1:
            out.append(sep)
    out.append(bot)

    return "\n".join(out)


def wrap_tables_in_code_blocks(text: str) -> str:
    """Finds blocks of lines starting with pipes, converts to Box-Drawing if they are tables."""
    from agent.markdown_tables import is_table_divider

    def replacement(match):
        block = match.group(1)
        lines = block.strip().split("\n")

        # Verify this is a real table (must have a divider row)
        has_divider = any(is_table_divider(line) for line in lines)
        if not has_divider:
            return block

        try:
            aligned_table = to_box_table(block)
        except Exception as e:
            logger.error(f"Box table conversion failed: {e}")
            aligned_table = realign_markdown_tables(block)

        if "```" in block:
            return block

        return f"\n{TEMPLATES['table_block'].format(content=aligned_table.strip())}\n"

    parts = re.split(r"(```[\s\S]*?```)", text)
    processed_parts = []
    for part in parts:
        if part.startswith("```"):
            processed_parts.append(part)
        else:
            processed_parts.append(TABLE_BLOCK_RE.sub(replacement, part))

    return "".join(processed_parts)


def _on_transform_llm_output(text: str, **_: Any) -> Optional[str]:
    """Hook implementation."""
    try:
        new_text = wrap_tables_in_code_blocks(text)
        if new_text != text:
            return new_text
    except Exception as e:
        logger.error(f"Failed to transform LLM output: {e}")
    return None


def register(ctx) -> None:
    ctx.register_hook("transform_llm_output", _on_transform_llm_output)
