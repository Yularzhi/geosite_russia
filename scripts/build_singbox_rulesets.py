from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"

import sys

sys.path.insert(0, str(ROOT))

from scripts.build_shared import ROOT_TAGS

RULE_PREFIXES = {
    "full:": "domain",
    "keyword:": "domain_keyword",
    "regexp:": "domain_regex",
}


def strip_inline_comment(line: str) -> str:
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.strip()


def parse_rule(line: str) -> tuple[str, str] | None:
    line = strip_inline_comment(line)
    if not line:
        return None

    for prefix, field in RULE_PREFIXES.items():
        if line.startswith(prefix):
            value = line[len(prefix) :].strip()
            if not value:
                raise ValueError(f"Empty value for rule prefix: {prefix}")
            return field, value

    if line.startswith("domain:"):
        value = line[len("domain:") :].strip()
        if not value:
            raise ValueError("Empty value for domain rule")
        return "domain_suffix", value

    if line.startswith(("include:", "geosite:")):
        raise ValueError(f"Unsupported nested rule line in generated data: {line}")

    if ":" in line:
        raise ValueError(f"Unsupported rule line: {line}")

    return "domain_suffix", line


def load_rules(tag: str) -> dict[str, list[str]]:
    path = DATA_DIR / tag
    if not path.exists():
        raise FileNotFoundError(f"Missing data file: {path}")

    grouped: dict[str, list[str]] = {
        "domain": [],
        "domain_suffix": [],
        "domain_keyword": [],
        "domain_regex": [],
    }
    seen: dict[str, set[str]] = {key: set() for key in grouped}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        parsed = parse_rule(raw_line)
        if not parsed:
            continue

        field, value = parsed
        if field not in grouped:
            raise ValueError(f"Unsupported Sing-box rule field: {field}")
        if value in seen[field]:
            continue

        seen[field].add(value)
        grouped[field].append(value)

    return grouped


def build_rule_set(tag: str) -> dict[str, object]:
    grouped = load_rules(tag)
    rules: list[dict[str, list[str]]] = []

    for field in ("domain", "domain_suffix", "domain_keyword", "domain_regex"):
        values = grouped[field]
        if values:
            rules.append({field: values})

    return {
        "version": 5,
        "rules": rules,
    }


def cleanup_output_dir(output_dir: Path) -> None:
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)


def build(output_dir: Path) -> None:
    cleanup_output_dir(output_dir)

    for tag in ROOT_TAGS:
        source = build_rule_set(tag)
        out_path = output_dir / f"{tag}.json"
        out_path.write_text(
            json.dumps(source, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"Wrote {out_path}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build sing-box rule-set source files")
    parser.add_argument("--output-dir", required=True, help="Directory for generated JSON source files")
    args = parser.parse_args()

    build(Path(args.output_dir))


if __name__ == "__main__":
    main()
