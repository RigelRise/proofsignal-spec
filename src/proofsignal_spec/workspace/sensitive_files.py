from __future__ import annotations

import fnmatch
from pathlib import Path

DEFAULT_SENSITIVE_PATTERNS = [
    ".env",
    ".env.*",
    "**/.env",
    "**/.env.*",
    "*secret*",
    "*credentials*",
    "*.pem",
    "*.key",
    "*.p12",
    "*.pfx",
    "id_rsa",
    "id_ed25519",
    ".ssh/**",
    ".aws/**",
    ".gcloud/**",
    "secrets/**",
]


def is_sensitive_path(path: str | Path, patterns: list[str] | None = None) -> bool:
    rel = Path(path).as_posix()
    names = [rel, Path(rel).name]
    for pattern in patterns or DEFAULT_SENSITIVE_PATTERNS:
        if any(fnmatch.fnmatch(name, pattern) for name in names):
            return True
    return False


def filter_safe_paths(paths: list[str | Path], patterns: list[str] | None = None) -> tuple[list[str], list[str]]:
    safe: list[str] = []
    blocked: list[str] = []
    for path in paths:
        rel = Path(path).as_posix()
        if is_sensitive_path(rel, patterns):
            blocked.append(rel)
        else:
            safe.append(rel)
    return safe, blocked


def requires_approval(path: str | Path, patterns: list[str] | None = None) -> bool:
    return is_sensitive_path(path, patterns)
