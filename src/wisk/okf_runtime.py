"""OKF-parser-owned typed read/write boundary for Wisk runtime state."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

from okf_parser import load_bundle
from okf_parser.apply import apply_bundle

from wisk.work_run import WorkRunWisk

_SPEC_TEMPLATE = "../specs/{slug}.md"


class OKFWorkRunWisk(WorkRunWisk):
    """Work runtime that delegates generic OKF typing and mutation to okf-parser."""

    @classmethod
    def open(cls, path: str | Path = "knowledge") -> OKFWorkRunWisk:
        root = Path(path).resolve()
        return cls(bundle=load_bundle(root), root_path=root)

    def _typed_trace_components(
        self,
        mapping: dict[str, str],
        run_id: str,
    ) -> dict[str, list[dict[str, Any]]]:
        """Materialize every Raw child through declared okf-parser relations."""
        bundle = self._reload()
        result: dict[str, list[dict[str, Any]]] = {}
        with bundle.compile_types(_SPEC_TEMPLATE) as typed:
            missing = sorted(
                {
                    concept_type
                    for concept_type in mapping.values()
                    if concept_type not in typed.tables
                }
            )
            if missing:
                concepts = ", ".join(missing)
                raise ValueError(
                    "Raw trace types require declared .schema.sql contracts; "
                    f"missing from okf-parser TypedRelations: {concepts}"
                )
            for name, concept_type in mapping.items():
                relation = typed[concept_type]
                if "run" not in relation.columns:
                    raise ValueError(
                        f"Raw trace type {concept_type} must declare a run column in its schema"
                    )
                frame = relation.filter(relation["run"] == run_id).execute()
                records: list[dict[str, Any]] = []
                for _, row in frame.iterrows():
                    frontmatter: dict[str, Any] = {}
                    for column in frame.columns:
                        key = str(column)
                        if key.startswith("__okf_"):
                            continue
                        value = self._runtime_value(row[column])
                        if value is not None:
                            frontmatter[key] = value
                    records.append(frontmatter)
                result[name] = records
        return result

    def _apply_record_fields(
        self,
        concept_type: str,
        record: dict[str, Any],
        updates: dict[str, object],
    ) -> dict[str, object]:
        """Patch one existing concept through okf-parser's transactional apply writer."""
        if not updates:
            return {"succeeded": True, "written": False, "changed_paths": []}
        relative_path = str(record["path"])
        assignments = ", ".join(
            f"{self._sql_identifier(field)} = {self._sql_literal(value)}"
            for field, value in updates.items()
        )
        # Identifiers/scalars are bounded above; remove this bridge after okf-parser #257.
        sql = (
            f"UPDATE {self._sql_identifier(concept_type)} SET {assignments} "  # nosec B608
            f"WHERE __okf_path = {self._sql_literal(relative_path)}"
        )
        result = apply_bundle(
            str(self.root_path),
            sql=sql,
            write=True,
            spec_template=_SPEC_TEMPLATE,
        )
        if not bool(result.get("succeeded")):
            error = str(result.get("error") or "okf-parser apply failed")
            raise RuntimeError(error)
        self._reload()
        return result

    @staticmethod
    def _sql_identifier(value: str) -> str:
        """Quote an internal OKF relation/field identifier for bounded apply SQL."""
        return '"' + str(value).replace('"', '""') + '"'

    @staticmethod
    def _sql_literal(value: object) -> str:
        """Render the small scalar domain Wisk currently patches through apply_bundle."""
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, int):
            return str(value)
        if isinstance(value, float):
            if not math.isfinite(value):
                raise ValueError("non-finite floats cannot be persisted as OKF scalar updates")
            return repr(value)
        if isinstance(value, str):
            return "'" + value.replace("'", "''") + "'"
        raise TypeError(
            "okf-parser apply bridge only accepts scalar field updates; "
            "structured writes belong to the public concept-write API"
        )
