# Modular Refactoring for Hermes CLI

## Summary

This refactoring improves modularity and maintainability, with specific optimizations for Linux systems.

## Changes Made

### Python Backend (`hermes_cli/`)

#### New Module Structure
```
hermes_cli/
├── core/                    # Core utilities (cross-platform)
│   ├── __init__.py
│   └── formatting.py        # Duration/token formatting, text cleaning
├── linux/                   # Linux-specific utilities
│   ├── __init__.py
│   └── clipboard.py         # wl-clipboard, xclip, xsel integration
├── tui/                     # Terminal UI components (planned)
├── commands/                # CLI command handlers (planned)
└── gateway/                 # Gateway communication (planned)
```

#### Key Extractions
- **formatting.py**: `format_duration_compact()`, `format_token_count_compact()`, `strip_reasoning_tags()`
- **linux/clipboard.py**: Auto-detect and use available Linux clipboard tools

### TypeScript Frontend (`web/src/lib/api/`)

#### New Module Structure
```
web/src/lib/api/
├── index.ts                 # Main exports
├── types.ts                 # Shared TypeScript interfaces
├── http.ts                  # HTTP utilities (fetchJSON, session handling)
├── auth.ts                  # Authentication API
└── sessions.ts              # Session management API
```

#### Benefits
- Split 1,950-line `api.ts` into focused modules
- Type-safe API calls with shared interfaces
- Easier to test and maintain individual concerns

### Linux System Scripts (`scripts/lib/linux/`)

#### New Scripts
- **systemd.sh**: Manage Hermes as a systemd service
  - Create, start, stop, restart, enable, disable services
  - Automatic service file generation
  
- **dependencies.sh**: Install Linux dependencies
  - Multi-distro support (Ubuntu/Debian, Fedora/RHEL, Arch/Manjaro)
  - Clipboard tools, browser deps, Python, uv package manager

## Usage Examples

### Linux Clipboard (Python)
```python
from hermes_cli.linux import copy_to_clipboard, paste_from_clipboard

copy_to_clipboard("Hello from Hermes!")
text = paste_from_clipboard()
```

### Formatting Utilities (Python)
```python
from hermes_cli.core import format_duration_compact, format_token_count_compact

print(format_duration_compact(3661))  # "1h 1m"
print(format_token_count_compact(1500000))  # "1.5M"
```

### API Client (TypeScript)
```typescript
import { sessionsApi, authApi } from '@/lib/api';

const sessions = await sessionsApi.getSessions(20, 0);
await authApi.logout();
```

### Systemd Service (Bash)
```bash
# Create and enable service
./scripts/lib/linux/systemd.sh create /opt/hermes myuser 8080
./scripts/lib/linux/systemd.sh enable
./scripts/lib/linux/systemd.sh start

# Check status
./scripts/lib/linux/systemd.sh status
```

### Install Dependencies (Bash)
```bash
# Install all dependencies
./scripts/lib/linux/dependencies.sh all

# Install only clipboard tools
./scripts/lib/linux/dependencies.sh clipboard
```

## Next Steps

### High Priority
1. Extract TUI components to `hermes_cli/tui/`
2. Split remaining `cli.py` functions into `hermes_cli/commands/`
3. Complete API module split (models, config, analytics)

### Medium Priority
4. Add Linux process management module
5. Create pre-commit hooks for code quality
6. Add comprehensive tests for new modules

### Lower Priority
7. Document all public APIs
8. Add type hints to remaining Python files
9. Create migration guide for plugin developers

## Testing

Verify the changes work:
```bash
# Test Python imports
python3 -c "from hermes_cli.core import format_duration_compact; print(format_duration_compact(120))"
python3 -c "from hermes_cli.linux import get_linux_clipboard_tool; print(get_linux_clipboard_tool())"

# Test TypeScript compilation
cd web && npm run check

# Test Linux scripts (requires sudo for systemd)
./scripts/lib/linux/dependencies.sh python
```
