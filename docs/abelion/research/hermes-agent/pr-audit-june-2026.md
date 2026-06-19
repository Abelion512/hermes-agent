# Hermes Agent PR Audit — June 2026

## Completed

### PR 1: `write_text()` encoding fix
- **Branch:** `pr/write-text-encoding`
- **File:** `gateway/delivery.py:276,289`
- **Issue:** `write_text()` without `encoding="utf-8"` — relies on system default, breaks on Windows/non-UTF-8
- **Fix:** Added explicit `encoding="utf-8"` to both calls
- **Status:** ✅ Pushed

### PR 2: SQL allowlist validation
- **Branch:** `pr/sql-safe-queries`
- **File:** `hermes_state.py:4425`
- **Issue:** `_fts_table_exists(name)` interpolates table name into SQL without validation
- **Fix:** Added allowlist check against `_FTS_TABLES` before query
- **Status:** ✅ Pushed

## Findings (no fix needed)

- `auth.py` token writes — already uses `os.open(O_EXCL)` + `0o600` (secure)
- `optimize_fts()` — table names from hardcoded tuple (safe)
- SSL verification — clean, no `verify=False`
- Hardcoded secrets — none found

## Next Targets

- `hermes_state.py` — `f"DELETE FROM {table_name}"` at line 749 (in `_rebuild_fts_indexes`, table names are hardcoded — low risk but could use allowlist)
- `api_server.py` — `f"DELETE FROM conversations WHERE response_id IN ({placeholders})"` — placeholders use `?` params (safe)
- npm audit — web/ui-tui workspaces (optional fix)
