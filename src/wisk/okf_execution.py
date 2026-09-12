"""okf-parser boundary for RFC 0003 command execution."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Self

from okf_parser import load_bundle
from okf_parser.apply import apply_bundle

from wisk.execution import ExecutionWisk
from wisk.okf_runtime import OKFWorkRunWisk


class OKFExecutionWisk(ExecutionWisk, OKFWorkRunWisk):
    """Execution runtime using parser-owned typing and existing-record patches."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> Self:
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def _update_execution_next(self, execution: str, next_after: str | None) -> None:
        record = self._find_record("RunExecution", execution)
        # In okf-parser 0.45.9, declared columns are generated read projections.
        # Patch this optional string through the untyped writer instead; it preserves
        # untouched frontmatter, body, validation and transactional conflict checks.
        # The column may not exist yet when no execution has authored next_after.
        # Avoid a no-op ALTER: this parser version rejects it as touching no table.
        has_next = any(
            "next_after" in item["frontmatter"] for item in self._records("RunExecution")
        )
        add_column = (
            "" if has_next else 'ALTER TABLE "RunExecution" ADD COLUMN "next_after" VARCHAR; '
        )
        result = apply_bundle(
            str(self.root_path),
            sql=(
                add_column
                + f'UPDATE "RunExecution" SET "next_after" = {self._sql_literal(next_after)} '  # nosec B608
                f"WHERE __okf_path = {self._sql_literal(str(record['path']))}"
            ),
            write=True,
        )
        if not result.get("succeeded"):
            raise RuntimeError(str(result.get("error") or "okf-parser apply failed"))
        self._reload()

    def execute_command(self, *args: Any, **kwargs: Any) -> dict[str, Any]:
        """Execute while normalizing display newlines without changing raw byte digests."""
        result = super().execute_command(*args, **kwargs)
        result["stdout"] = self._normalize_display_output(str(result.get("stdout") or ""))
        result["stderr"] = self._normalize_display_output(str(result.get("stderr") or ""))
        return result

    @staticmethod
    def _normalize_display_output(value: str) -> str:
        return value.replace("\r\n", "\n")
