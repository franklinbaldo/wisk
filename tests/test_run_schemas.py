from pathlib import Path

from wisk.models import generate_pydantic_code, get_schema_contracts

ROOT = Path(__file__).parent.parent
RUN_TYPES = {
    "RunSpec",
    "LoopRun",
    "RunReading",
    "RunGoal",
    "RunDecision",
    "RunEvidence",
    "RunCheck",
    "RunOutcome",
}


def test_all_run_types_have_declared_schema_contracts() -> None:
    contracts = get_schema_contracts(ROOT / "knowledge")
    contract_types = {contract.concept_type for contract in contracts}
    assert contract_types >= RUN_TYPES


def test_all_run_types_export_pydantic_models_without_instances() -> None:
    code = generate_pydantic_code(ROOT / "knowledge")
    for concept_type in RUN_TYPES:
        assert f"class {concept_type}Concept(BaseModel):" in code
