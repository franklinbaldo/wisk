from wisk import Wisk, __version__


def test_wisk_is_canonical_public_runtime_alias() -> None:
    assert Wisk is Wisk
    assert __version__
