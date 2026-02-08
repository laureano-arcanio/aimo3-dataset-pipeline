# Pipeline Utilities

This package contains utility modules used across all pipeline notebooks.

## Modules

### `llm_pool.py`
Bounded-concurrency async LLM client for OpenAI-compatible endpoints.

**Key Classes:**
- `LLMPool`: Main async LLM client with connection pooling
- `LLMRequestError`: Exception for non-retryable LLM request failures
- `LLMResponse`: Response container with content and token counts

**Features:**
- Configurable concurrency limits
- Automatic retry with exponential backoff
- Token usage tracking
- Timeout handling
- OpenAI-compatible API support

**Example Usage:**
```python
from utils import LLMPool

async with LLMPool(
    base_url="http://127.0.0.1:8080/v1",
    api_key="sk-local",
    model="gpt-oss",
    max_inflight=25,
    timeout=300,
) as pool:
    response = await pool.request(
        messages=[
            {"role": "system", "content": "You are helpful."},
            {"role": "user", "content": "What is 2+2?"}
        ],
        temperature=0.7,
        max_tokens=1024,
    )
    print(response.content)
    print(f"Tokens: {response.prompt_tokens} + {response.completion_tokens}")
```

### `runtime_config.py`
Hot-reloadable JSON configuration for live parameter updates.

**Key Class:**
- `RuntimeConfig`: Configuration manager that can reload from JSON file

**Features:**
- Live configuration updates without restart
- Change tracking and notifications
- Type-safe field access
- Automatic save to disk
- Default value support

**Example Usage:**
```python
from utils import RuntimeConfig

cfg = RuntimeConfig("config.json", defaults={
    "MAX_CONCURRENT_REQUESTS": 25,
    "LLM_REQUEST_TIMEOUT_SECONDS": 300,
    "EXECUTION_TIMEOUT_SECONDS": 30,
})

# Access config values
print(cfg.MAX_CONCURRENT_REQUESTS)

# Reload config from disk (picks up external edits)
changed = cfg.reload()
if changed:
    print(f"Config updated: {changed}")

# Save current values
cfg.save()
```

## Usage in Notebooks

All notebooks should import utilities using:

```python
from utils import LLMPool, RuntimeConfig
```

**Do NOT use:**
```python
# ❌ Wrong - old import style
from llm_pool import LLMPool
from runtime_config import RuntimeConfig

# ❌ Wrong - path manipulation
import sys
sys.path.insert(0, ...)
```

## Package Structure

```
utils/
├── __init__.py           # Package initialization with exports
├── llm_pool.py          # Async LLM client
├── runtime_config.py    # Hot-reloadable config
└── README.md            # This file
```

## Development

When adding new utilities:

1. Create the module file in this directory
2. Add exports to `__init__.py`:
   ```python
   from .new_module import NewClass
   __all__.append("NewClass")
   ```
3. Document in this README
4. Update notebooks to import from `utils`

## Testing

To test imports work correctly:

```python
# Should work from any notebook
from utils import LLMPool, RuntimeConfig

# Check what's available
import utils
print(dir(utils))
```

## Migration Notes

**Previous Location:** `pipeline/llm_pool.py`, `pipeline/runtime_config.py`  
**New Location:** `pipeline/utils/`  
**Migration Date:** February 8, 2026

All notebooks have been updated to use the new import path. No path manipulation is needed.
