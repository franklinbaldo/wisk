"""Pydantic model generation and typed query helpers derived from OKF contracts."""

from __future__ import annotations

from typing import TYPE_CHECKING

from okf_parser.schema_export import TypeContract, build_schema_contracts, export_pydantic_source

if TYPE_CHECKING:
    from pathlib import Path

SPEC_TEMPLATE = "../specs/{slug}.md"


def generate_pydantic_code(knowledge_path: Path) -> str:
    """Generate Pydantic models from observed and declared OKF contracts."""
    return export_pydantic_source(
        str(knowledge_path),
        spec_template=SPEC_TEMPLATE,
    )


def get_schema_contracts(knowledge_path: Path) -> tuple[TypeContract, ...]:
    """Inspect observed and contract-first schemas discovered by okf-parser."""
    return build_schema_contracts(
        str(knowledge_path),
        spec_template=SPEC_TEMPLATE,
    )
