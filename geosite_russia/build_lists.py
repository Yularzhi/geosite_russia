"""Main builder — fetches upstream lists, normalises domains, generates data/ tags."""

from __future__ import annotations

import logging
import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import yaml
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Normal package import — no sys.path hacks needed.
from geosite_russia.shared import ROOT_TAGS, load_domain_file, strip_inline_comment

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SOURCES_DIR = ROOT / "sources"

# ── Load config ─────────────────────────────────────────────────────────────

CONFIG_PATH = SOURCES_DIR / "config.yaml"


def load_config() -> dict:
    """Load and return configuration from sources/config.yaml."""
    with open(CONFIG_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f)


SRC = load_config()

ROOT_TAG_SOURCE = SRC["root_tag_source"]

RU_EXCLUDED_SUFFIXES = set(SRC["ru_excluded_suffixes"])
RU_TLDS = tuple(SRC["ru_tlds"])

ADS_EXCLUDED_DOMAINS = set(SRC.get("excluded_domains", {}).get("category-ads-all", []))

MANUAL_RU_BLOCKED_FILE = SOURCES_DIR / SRC["manual_ru_blocked_file"]
APPLE_DIRECT_FILE = SOURCES_DIR / SRC["apple_direct_file"]
CATEGORY_RU_DIRECT_FILE = SOURCES_DIR / SRC["category_ru_direct_file"]

DLC_BASE = SRC["dlc_base"]
PROXY_URL = SRC["proxy_url"]
ANTIFILTER_RU_BLOCKED_URL = SRC["antifilter_ru_blocked_url"]
HAGEZI_LIGHT_URLS = SRC["hagezi_light_urls"]
PETER_LOWE_URL = SRC["peter_lowe_url"]

HTTP_TIMEOUT = SRC["http"]["timeout"]
RETRY_TOTAL = SRC["http"]["retries"]["total"]
RETRY_BACKOFF = SRC["http"]["retries"]["backoff_factor"]
RETRY_STATUSES = tuple(SRC["http"]["retries"]["status_forcelist"])

SESSION = None  # created lazily


def _make_session() -> object:
    """Create a requests Session with retry logic."""
    import requests

    session = requests.Session()
    ua = SRC["http"]["user_agent"]
    session.headers.update({"User-Agent": ua})

    retry_strategy = Retry(
        total=RETRY_TOTAL,
        backoff_factor=RETRY_BACKOFF,
        status_forcelist=list(RETRY_STATUSES),
        allowed_methods=["GET"],
    )
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)
    return session


DOMAIN_RE = re.compile(r"^(?:[a-z0-9-]+\.)+[a-z]{2,63}$")


def get_session() -> object:
    global SESSION
    if SESSION is None:
        SESSION = _make_session()
    return SESSION


# ── Domain normalization ────────────────────────────────────────────────────


def normalize_text_domain(line: str) -> str | None:
    line = line.strip().lower()

    if not line:
        return None
    if line.startswith("#") or line.startswith("//") or line.startswith(";"):
        return None

    line = line.replace("\t", " ").split(" ")[0].strip()

    if line.startswith("http://") or line.startswith("https://"):
        parsed = urlparse(line)
        line = parsed.hostname or ""
    else:
        line = line.split("://", 1)[-1]

    line = line.strip().strip(".")
    if line.startswith("*."):
        line = line[2:]
    if line.startswith("."):
        line = line[1:]

    line = line.split("/", 1)[0]

    if ":" in line and line.count(":") == 1:
        host, port = line.split(":", 1)
        if port.isdigit():
            line = host

    if not line or "_" in line or line.endswith(".local"):
        return None

    return line if DOMAIN_RE.match(line) else None


# ── File I/O (atomic write) ─────────────────────────────────────────────────


def write_tag(tag: str, lines: list[str]) -> None:
    """Write tag file atomically via tmp + os.rename."""
    path = DATA_DIR / tag
    content = "\n".join(lines).strip() + "\n"
    tmp_path = str(path) + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        f.write(content)
    shutil.move(tmp_path, str(path))


def cleanup_data_dir() -> None:
    """Remove all files/dirs inside data/ to start fresh."""
    if not DATA_DIR.exists():
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        return
    for item in DATA_DIR.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


# ── HTTP helpers ────────────────────────────────────────────────────────────


def fetch_text(url: str, *, timeout: int | None = None) -> str:
    """Fetch text content from URL with automatic retry on transient errors."""
    if timeout is None:
        timeout = HTTP_TIMEOUT
    sess = get_session()
    resp = sess.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch_lines(url: str) -> list[str]:
    return fetch_text(url).splitlines()


# ── DLC parsing & flattening ────────────────────────────────────────────────


def split_attrs(line: str) -> tuple[str, set[str]]:
    parts = line.split()
    if not parts:
        return "", set()

    base_parts = []
    attrs = set()

    for part in parts:
        if part.startswith("@"):
            attrs.add(part[1:])
        else:
            base_parts.append(part)

    return " ".join(base_parts).strip(), attrs


def parse_upstream_line(line: str) -> tuple[str, str, set[str]] | None:
    line = strip_inline_comment(line)
    if not line:
        return None

    base, attrs = split_attrs(line)
    if not base:
        return None

    if base.startswith("include:"):
        child = base.split(":", 1)[1].strip()
        if child:
            return ("include", child, attrs)
        return None

    return ("rule", base, attrs)


def rule_matches_attrs(rule_attrs: set[str], required_attrs: set[str] | None) -> bool:
    if not required_attrs:
        return True
    return rule_attrs.issuperset(required_attrs)


def merge_required_attrs(
    parent_required: set[str] | None,
    local_attrs: set[str],
) -> set[str] | None:
    if parent_required and local_attrs:
        return set(parent_required) | set(local_attrs)
    if parent_required:
        return set(parent_required)
    if local_attrs:
        return set(local_attrs)
    return None


def get_tag_url(tag: str) -> str:
    source = ROOT_TAG_SOURCE.get(tag, "dlc")

    if source == "dlc":
        return DLC_BASE + tag

    raise ValueError(f"Unknown source for tag: {tag}")


def flatten_rules(
    tag: str,
    required_attrs: set[str] | None = None,
    seen: set[tuple[str, tuple[str, ...]]] | None = None,
) -> list[str]:
    if seen is None:
        seen = set()

    seen_key = (tag, tuple(sorted(required_attrs or set())))
    if seen_key in seen:
        return []

    seen.add(seen_key)

    try:
        text = fetch_text(get_tag_url(tag))
    except Exception as e:  # noqa: BLE001
        log.warning("Skipping missing DLC include: %s (%s)", tag, e)
        return []

    rules: list[str] = []

    for raw_line in text.splitlines():
        parsed = parse_upstream_line(raw_line)
        if not parsed:
            continue

        kind, value, attrs = parsed

        if kind == "include":
            child_required_attrs = merge_required_attrs(required_attrs, attrs)
            rules.extend(flatten_rules(value, child_required_attrs, seen))
        else:
            if rule_matches_attrs(attrs, required_attrs):
                rules.append(value)

    return rules


def dedupe_keep_order(items: list[str]) -> list[str]:
    seen = set()
    result = []
    for item in items:
        if item not in seen:
            seen.add(item)
            result.append(item)
    return result


# ── Tag builders ────────────────────────────────────────────────────────────


def extract_plain_domains_from_rules(rules: list[str]) -> set[str]:
    result: set[str] = set()

    for rule in rules:
        rule = rule.strip()
        if not rule:
            continue
        if rule.startswith(("full:", "keyword:", "regexp:", "domain:", "include:")):
            continue

        domain = normalize_text_domain(rule)
        if domain:
            result.add(domain)

    return result


def is_ru_excluded_domain(domain: str) -> bool:
    for suffix in RU_EXCLUDED_SUFFIXES:
        if domain == suffix or domain.endswith("." + suffix):
            return True

    return any(domain.endswith(tld) for tld in RU_TLDS)


def build_ru_blocked() -> list[str]:
    """Build ru-blocked from legacy upstream sources plus manual domains."""
    domains: set[str] = set()

    try:
        for line in fetch_lines(ANTIFILTER_RU_BLOCKED_URL):
            domain = normalize_text_domain(line)
            if domain:
                domains.add(domain)
    except Exception as e:  # noqa: BLE001
        log.error("Failed to fetch antifilter list from %s: %s", ANTIFILTER_RU_BLOCKED_URL, e)

    category_ru_domains = extract_plain_domains_from_rules(flatten_rules("category-ru"))

    try:
        for line in fetch_lines(PROXY_URL):
            domain = normalize_text_domain(line)
            if not domain or domain in category_ru_domains or is_ru_excluded_domain(domain):
                continue
            domains.add(domain)
    except Exception as e:  # noqa: BLE001
        log.error("Failed to fetch proxy list from %s: %s", PROXY_URL, e)

    for domain in load_domain_file(MANUAL_RU_BLOCKED_FILE, normalize_text_domain):
        domains.add(domain)

    sorted_domains = sorted(domains)
    write_tag("ru-blocked", sorted_domains)
    log.info("RU blocked total: %d domains", len(sorted_domains))
    return sorted_domains


def build_ads() -> list[str]:
    domains: set[str] = set()

    # DLC category-ads-all
    try:
        for rule in flatten_rules("category-ads-all"):
            rule = rule.strip()
            if not rule or rule.startswith(("full:", "keyword:", "regexp:", "domain:", "include:")):
                continue
            domain = normalize_text_domain(rule)
            if domain and domain not in ADS_EXCLUDED_DOMAINS:
                domains.add(domain)
    except Exception as e:  # noqa: BLE001
        log.error("Failed to build ads from DLC: %s", e)

    # HaGeZi Light
    hagezi_fetched = False
    for url in HAGEZI_LIGHT_URLS:
        try:
            for line in fetch_text(url).splitlines():
                domain = normalize_text_domain(line)
                if domain and domain not in ADS_EXCLUDED_DOMAINS:
                    domains.add(domain)
            hagezi_fetched = True
            break
        except Exception as e:  # noqa: BLE001
            log.warning("HaGeZi Light failed from %s: %s", url, e)

    if not hagezi_fetched:
        log.error("All HaGeZi Light mirrors failed")

    # Peter Lowe
    try:
        for line in fetch_text(PETER_LOWE_URL).splitlines():
            domain = normalize_text_domain(line)
            if domain and domain not in ADS_EXCLUDED_DOMAINS:
                domains.add(domain)
    except Exception as e:  # noqa: BLE001
        log.error("Failed to fetch Peter Lowe list from %s: %s", PETER_LOWE_URL, e)

    sorted_domains = sorted(domains)
    write_tag("category-ads-all", sorted_domains)
    log.info("ADS total: %d domains", len(sorted_domains))
    return sorted_domains


def build_flat_root_tags() -> dict[str, list[str]]:
    """Build all root-level tags (excluding category-ads-all handled separately)."""
    results: dict[str, list[str]] = {}

    for tag in ROOT_TAGS:
        if tag == "category-ads-all":
            continue

        log.info("Building tag: %s", tag)

        if tag == "viber":
            rules = flatten_rules("viber")
            rules.extend(flatten_rules("rakuten"))
        elif tag == "category-ru":
            rules = flatten_rules(tag)
            rules.extend(load_category_ru_direct_domains())
        elif tag == "apple":
            rules = load_apple_direct_domains()
        else:
            rules = flatten_rules(tag)

        rules = dedupe_keep_order(rules)
        write_tag(tag, rules)
        results[tag] = rules
        log.info("Tag %s: %d entries", tag, len(rules))

    return results


# ── Helper loaders ──────────────────────────────────────────────────────────


def load_apple_direct_domains() -> list[str]:
    """Load apple direct domains from sources/apple.txt"""
    return load_domain_file(APPLE_DIRECT_FILE, normalize_text_domain)


def load_category_ru_direct_domains() -> list[str]:
    """Load category-ru direct domains from sources/category-ru-direct.txt"""
    return load_domain_file(CATEGORY_RU_DIRECT_FILE, normalize_text_domain)


# ── Validation ──────────────────────────────────────────────────────────────


REQUIRED_MIN_DOMAINS: dict[str, int] = {
    "ru-blocked": 500,
    "category-ads-all": 1000,
    "category-ru": 100,
    "telegram": 1,
    "viber": 1,
    "whatsapp": 1,
    "meta": 1,
    "facebook": 1,
    "google": 1,
    "private": 1,
}


def validate_output(
    min_domains: dict[str, int] | None = None,
    data_dir: Path | None = None,
) -> list[str]:
    """Validate that generated data files are non-empty and meet minimum thresholds.

    Returns a list of error strings; empty list means success.
    Can accept a custom ``data_dir`` for unit testing.
    """
    if min_domains is None:
        min_domains = REQUIRED_MIN_DOMAINS

    if data_dir is None:
        data_dir = DATA_DIR

    errors: list[str] = []

    for tag, min_count in min_domains.items():
        path = data_dir / tag
        if not path.exists():
            errors.append(f"[{tag}] File missing")
            continue

        count = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())

        if count < min_count:
            errors.append(f"[{tag}] Only {count} domains (minimum: {min_count})")

    return errors


# ── Main ────────────────────────────────────────────────────────────────────


def main() -> None:
    cleanup_data_dir()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    SOURCES_DIR.mkdir(parents=True, exist_ok=True)

    build_ru_blocked()
    build_ads()
    build_flat_root_tags()

    # Validate output before returning success
    errors = validate_output()
    if errors:
        log.error("Validation FAILED:")
        for err in errors:
            log.error("  %s", err)
        sys.exit(1)

    log.info("All validations passed.")
    log.info("Done.")


if __name__ == "__main__":
    main()
