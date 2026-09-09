"""Non-destructive bootstrap and upgrade for Wisk consumer repositories."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from pathlib import Path
from typing import Any

from okf_parser.service import check_bundle

MANIFEST_FORMAT_VERSION = 1
DEFAULT_PROFILE = "standard"

_CANONICAL_SOURCES = {
    "knowledge/system/canonical/session-types/work.md": "session-types/work.md",
    "knowledge/system/canonical/session-types/experience.md": "session-types/experience.md",
    "knowledge/system/canonical/session-types/wiki.md": "session-types/wiki.md",
    "knowledge/system/canonical/session-types/skill.md": "session-types/skill.md",
    "knowledge/system/canonical/run-specs/work.md": "run-specs/work.md",
    "knowledge/system/canonical/run-specs/experience.md": "run-specs/experience.md",
    "knowledge/system/canonical/run-specs/wiki.md": "run-specs/wiki.md",
    "knowledge/system/canonical/run-specs/skill.md": "run-specs/skill.md",
}
_PRESERVED_PREFIXES = (
    Path("knowledge/local"),
    Path("knowledge/experiences"),
    Path("knowledge/wiki"),
    Path("knowledge/skills"),
)
_MANAGED_GITIGNORE = b"/.gitignore\n/manifest.json\n/specs/\n/knowledge/system/\n"


def _package_root() -> Path:
    return Path(__file__).resolve().parent


def _source_repository_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _spec_source_root() -> Path:
    packaged = _package_root() / "_assets" / "specs"
    if packaged.is_dir():
        return packaged
    source = _source_repository_root() / "specs"
    if source.is_dir():
        return source
    raise RuntimeError("Wisk normative specs are not available in this installation")


def _canonical_source(relative: str) -> Path:
    packaged = _package_root() / "_assets" / "canonical" / relative
    if packaged.is_file():
        return packaged
    source = _source_repository_root() / "knowledge" / "skills" / relative
    if source.is_file():
        return source
    raise RuntimeError(f"Wisk canonical asset is not available: {relative}")


def _profile_source_root(profile: str) -> Path:
    root = _package_root() / "profiles" / profile
    if not root.is_dir():
        raise ValueError(f"Unknown Wisk bootstrap profile: {profile}")
    return root


def _sha256(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def _managed_assets(profile: str) -> dict[str, bytes]:
    assets: dict[str, bytes] = {".gitignore": _MANAGED_GITIGNORE}
    for source in sorted(_spec_source_root().iterdir()):
        if source.is_file():
            assets[f"specs/{source.name}"] = source.read_bytes()
    for destination, relative in _CANONICAL_SOURCES.items():
        assets[destination] = _canonical_source(relative).read_bytes()
    profile_root = _profile_source_root(profile)
    for source in sorted(path for path in profile_root.rglob("*") if path.is_file()):
        relative = source.relative_to(profile_root).as_posix()
        assets[f"knowledge/system/profiles/{profile}/{relative}"] = source.read_bytes()
    return assets


def _manifest(profile: str, assets: dict[str, bytes]) -> dict[str, Any]:
    from wisk import __version__

    return {
        "format_version": MANIFEST_FORMAT_VERSION,
        "profile": profile,
        "wisk_version": __version__,
        "managed_files": {path: _sha256(content) for path, content in sorted(assets.items())},
    }


def _write_manifest(root: Path, manifest: dict[str, Any]) -> None:
    content = json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    (root / "manifest.json").write_text(content, encoding="utf-8")


def _read_manifest(root: Path) -> dict[str, Any] | None:
    path = root / "manifest.json"
    if not path.is_file():
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Invalid Wisk manifest: expected a JSON object")
    return data


def _write_assets(root: Path, assets: dict[str, bytes]) -> None:
    for relative, content in assets.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _snapshot_files(root: Path, relative_paths: set[str]) -> dict[str, bytes | None]:
    return {
        relative: (path.read_bytes() if path.is_file() else None)
        for relative in relative_paths
        for path in [root / relative]
    }


def _restore_files(root: Path, snapshot: dict[str, bytes | None]) -> None:
    for relative, content in snapshot.items():
        path = root / relative
        if content is None:
            path.unlink(missing_ok=True)
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(content)


def _existing_unmanaged_files(root: Path) -> list[Path]:
    if not root.is_dir():
        return []
    return sorted(path.relative_to(root) for path in root.rglob("*") if path.is_file())


def _preservable_state(paths: list[Path]) -> bool:
    return all(
        any(path == prefix or prefix in path.parents for prefix in _PRESERVED_PREFIXES)
        for path in paths
    )


def _validate_installation(root: Path) -> dict[str, object]:
    return check_bundle(
        str(root / "knowledge"),
        require_spec="../specs/{slug}.md",
        normative_spec=True,
    )


def init_repository(
    repository: str | Path = ".",
    *,
    profile: str = DEFAULT_PROFILE,
) -> dict[str, Any]:
    """Initialize one repository with the managed Wisk consumer bundle."""
    repo = Path(repository).resolve()
    if not repo.is_dir():
        raise ValueError(f"Repository path is not a directory: {repo}")

    target = repo / ".wisk"
    existing_manifest = _read_manifest(target) if target.is_dir() else None
    if existing_manifest is not None:
        return {
            "status": "already-initialized",
            "root": str(target),
            "profile": existing_manifest.get("profile"),
            "next": f"wisk upgrade {repo}",
        }

    unmanaged = _existing_unmanaged_files(target)
    if unmanaged and not _preservable_state(unmanaged):
        return {
            "status": "unmanaged-existing-state",
            "root": str(target),
            "files": [path.as_posix() for path in unmanaged],
            "message": (
                "Existing .wisk state outside consumer/runtime knowledge namespaces "
                "has no managed manifest; it was left untouched."
            ),
        }

    assets = _managed_assets(profile)
    created_target = not target.exists()
    target.mkdir(parents=True, exist_ok=True)
    try:
        _write_assets(target, assets)
        manifest = _manifest(profile, assets)
        _write_manifest(target, manifest)
        report = _validate_installation(target)
        if not bool(report["conformant"]):
            raise ValueError("Generated Wisk bundle is not conformant")
    except Exception:
        if created_target:
            shutil.rmtree(target, ignore_errors=True)
        else:
            for relative in assets:
                (target / relative).unlink(missing_ok=True)
            (target / "manifest.json").unlink(missing_ok=True)
        raise

    return {
        "status": "initialized",
        "root": str(target),
        "profile": profile,
        "managed_files": len(assets),
        "preserved_files": len(unmanaged),
        "conformant": True,
        "next": "wisk start",
    }


def _apply_upgrade(root: Path, old_managed: dict[str, str], assets: dict[str, bytes]) -> None:
    obsolete = set(old_managed) - set(assets)
    for relative in obsolete:
        (root / relative).unlink(missing_ok=True)
    _write_assets(root, assets)


def upgrade_repository(repository: str | Path = ".") -> dict[str, Any]:
    """Upgrade only Wisk-managed files, refusing edited managed state."""
    repo = Path(repository).resolve()
    target = repo / ".wisk"
    manifest = _read_manifest(target) if target.is_dir() else None
    if manifest is None:
        return {
            "status": "not-initialized",
            "root": str(target),
            "message": "No managed Wisk manifest found; run wisk init first.",
        }
    if manifest.get("format_version") != MANIFEST_FORMAT_VERSION:
        return {
            "status": "unsupported-manifest",
            "root": str(target),
            "format_version": manifest.get("format_version"),
            "supported_format_version": MANIFEST_FORMAT_VERSION,
        }

    profile = str(manifest.get("profile") or DEFAULT_PROFILE)
    assets = _managed_assets(profile)
    raw_old_managed = manifest.get("managed_files") or {}
    if not isinstance(raw_old_managed, dict):
        raise ValueError("Invalid Wisk manifest: managed_files must be an object")
    old_managed = {str(path): str(digest) for path, digest in raw_old_managed.items()}

    conflicts: list[str] = []
    for relative, old_digest in old_managed.items():
        path = target / relative
        if not path.is_file():
            continue
        current_digest = _sha256(path.read_bytes())
        new_content = assets.get(relative)
        new_digest = _sha256(new_content) if new_content is not None else None
        if current_digest != old_digest and current_digest != new_digest:
            conflicts.append(relative)
    if conflicts:
        return {
            "status": "conflict",
            "root": str(target),
            "conflicts": sorted(conflicts),
            "message": "Managed files were edited locally; no upgrade was written.",
        }

    new_manifest = _manifest(profile, assets)
    with tempfile.TemporaryDirectory(prefix=".wisk-upgrade-", dir=repo) as temporary:
        staged = Path(temporary) / ".wisk"
        shutil.copytree(target, staged)
        _apply_upgrade(staged, old_managed, assets)
        _write_manifest(staged, new_manifest)
        report = _validate_installation(staged)
        if not bool(report["conformant"]):
            return {
                "status": "invalid-upgrade",
                "root": str(target),
                "diagnostics": report.get("diagnostics", []),
                "message": "Candidate managed upgrade is not conformant; live state was untouched.",
            }

    touched = set(old_managed) | set(assets) | {"manifest.json"}
    snapshot = _snapshot_files(target, touched)
    try:
        _apply_upgrade(target, old_managed, assets)
        _write_manifest(target, new_manifest)
    except Exception:
        _restore_files(target, snapshot)
        raise

    return {
        "status": "upgraded",
        "root": str(target),
        "profile": profile,
        "managed_files": len(assets),
        "conformant": True,
    }
