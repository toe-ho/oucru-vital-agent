from __future__ import annotations

import functools
import time
from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass
class ToolResult:
    success: bool
    data: dict | None = None
    error_type: str | None = None
    error_detail: str | None = None
    duration_ms: int = 0


def tool_wrapper(fn: Callable) -> Callable:
    """
    Wraps a tool function to:
    - Time execution
    - Catch all exceptions and return ToolResult instead of raising
    - Ensure raw signal arrays never reach agent_logs (callers log only metadata)
    """
    @functools.wraps(fn)
    def wrapper(*args: Any, **kwargs: Any) -> ToolResult:
        start = time.monotonic()
        try:
            result = fn(*args, **kwargs)
            duration_ms = int((time.monotonic() - start) * 1000)
            return ToolResult(success=True, data=result, duration_ms=duration_ms)
        except FileNotFoundError as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return ToolResult(
                success=False,
                error_type="FileNotFoundError",
                error_detail=str(e),
                duration_ms=duration_ms,
            )
        except ValueError as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return ToolResult(
                success=False,
                error_type="ValueError",
                error_detail=str(e),
                duration_ms=duration_ms,
            )
        except Exception as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            return ToolResult(
                success=False,
                error_type=type(e).__name__,
                error_detail=str(e),
                duration_ms=duration_ms,
            )
    return wrapper
