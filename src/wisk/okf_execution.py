"""okf-parser boundary for RFC 0003 command execution."""

from __future__ import annotations

from typing import Any

from wisk.execution import ExecutionWisk
from wisk.okf_runtime import OKFWorkRunWisk


class OKFExecutionWisk(ExecutionWisk, OKFWorkRunWisk):
    """Execution runtime using parser-owned typing and existing-record patches."""

    def _update_execution_next(self, execution: str, next_after: str | None) -> None:
        record = self._find_record("RunExecution", execution)
        self._apply_record_fields("RunExecution", record, {"next_after": next_after})

    def execute_command(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Execute while normalizing display newlines without changing raw byte digests."""
        result = super().execute_command(*args, **kwargs)
        result["stdout"] = self._normalize_display_output(str(result.get("stdout") or ""))
        result["stderr"] = self._normalize_display_output(str(result.get("stderr") or ""))
        return result

    @staticmethod
    def _normalize_display_output(value: str) -> str:
        return value.replace("\r\n", "\n")
