import re

SYNONYM_MAP = {
    "oom": ["oom", "out of memory"],
    "ram": ["ram", "memory"],
    "dc": ["discord", "dc"],
    "tele": ["telegram", "tele"],
    "wag": ["whatsapp", "wag"],
    "ig": ["instagram", "ig"],
    "rag": ["rag", "retrieval"],
}

def expand_query(query_str: str) -> str:
    """
    Tokenizes input query string, maps slang/abbreviations to their synonyms,
    and returns a structured SQLite FTS5 query using AND and OR operators.
    """
    if not query_str or not query_str.strip():
        return ""

    # Clean punctuation and split by whitespace
    tokens = re.findall(r"\w+", query_str.lower())
    if not tokens:
        return ""

    fts_parts = []
    for token in tokens:
        if token in SYNONYM_MAP:
            # Expand synonyms using OR
            syns = SYNONYM_MAP[token]
            # Format each synonym correctly (quote multi-word terms)
            formatted_syns = []
            for s in syns:
                if " " in s:
                    formatted_syns.append(f'"{s}"')
                else:
                    formatted_syns.append(s)
            fts_parts.append(f"({' OR '.join(formatted_syns)})")
        else:
            # Prefix search for normal terms
            fts_parts.append(f"{token}*")

    return " AND ".join(fts_parts)
