from wisk import Wisk, WikiSkill, __version__


def test_wisk_is_canonical_public_runtime_alias() -> None:
    assert Wisk is WikiSkill
    assert __version__
