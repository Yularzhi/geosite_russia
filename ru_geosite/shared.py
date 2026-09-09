"""Shared utilities for source loading, domain normalization, and rule parsing."""

from __future__ import annotations

import os
import re
from collections.abc import Callable
from pathlib import Path

ROOT_TAGS = [
    "ru-blocked",
    "category-ads-all",
    "category-ru",
    "telegram",
    "viber",
    "whatsapp",
    "meta",
    "facebook",
    "google",
    "supercell",
    "roblox",
    "apple",
    "private",
]

DOMAIN_RE = re.compile(r"^(?:[a-z0-9-]+\.)+(?:[a-z]{2,63}|xn--[a-z0-9-]+)$")


def find_root() -> Path:
    """Locate the project root (the directory holding data/ and sources/).

    Resolution order: $GEOSITE_ROOT → package checkout layout → current
    directory. Keeps the console scripts (geosite-build, geosite-singbox)
    usable when the package is pip-installed outside a repository checkout.
    """
    env_root = os.environ.get("GEOSITE_ROOT")
    if env_root:
        return Path(env_root).expanduser().resolve()

    checkout_root = Path(__file__).resolve().parent.parent
    if (checkout_root / "sources" / "config.yaml").exists():
        return checkout_root

    return Path.cwd().resolve()


def strip_inline_comment(line: str) -> str:
    """Remove inline comments starting with '#' and return stripped line."""
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.strip()


def load_domain_file(file_path: Path, normalizer: Callable[[str], str | None] | None = None) -> list[str]:
    """Load lines from a file, stripping comments and optionally normalizing domains."""
    if not file_path.exists():
        return []

    results: list[str] = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw_line)
        if not line:
            continue
        if normalizer is not None:
            normalized = normalizer(line)
            if normalized:
                results.append(normalized)
        else:
            results.append(line)

    return results
