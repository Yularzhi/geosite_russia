from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path
from urllib.parse import urlparse

import requests
from urllib3.util.retry import Retry

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts.build_shared import ROOT_TAGS, load_domain_file, strip_inline_comment

DATA_DIR = ROOT / "data"
SOURCES_DIR = ROOT / "sources"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SOURCES_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "custom-geosite-builder/1.0"})

retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"],
)
adapter = requests.adapters.HTTPAdapter(max_retries=retry_strategy)
SESSION.mount("https://", adapter)
SESSION.mount("http://", adapter)

DOMAIN_RE = re.compile(r"^(?:[a-z0-9-]+\.)+[a-z]{2,63}$")

DLC_BASE = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"
PROXY_URL = "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/proxy.txt"
ANTIFILTER_RU_BLOCKED_URL = "https://community.antifilter.download/list/domains.txt"
HAGEZI_LIGHT_URLS = [
    "https://cdn.jsdelivr.net/gh/hagezi/dns-blocklists@latest/wildcard/light-onlydomains.txt",
    "https://raw.githubusercontent.com/hagezi/dns-blocklists/main/wildcard/light-onlydomains.txt",
]
PETER_LOWE_URL = "https://pgl.yoyo.org/adservers/serverlist.php?hostformat=plain&showintro=0&mimetype=plaintext"
MANUAL_RU_BLOCKED_FILE = SOURCES_DIR / "manual_ru_blocked.txt"
APPLE_DIRECT_FILE = SOURCES_DIR / "apple.txt"
CATEGORY_RU_DIRECT_FILE = SOURCES_DIR / "category-ru-direct.txt"

ROOT_TAG_SOURCE = {
    "category-ru": "dlc",
    "telegram": "dlc",
    "viber": "dlc",
    "whatsapp": "dlc",
    "meta": "dlc",
    "facebook": "dlc",
    "google": "dlc",
    "supercell": "dlc",
    "roblox": "dlc",
    "private": "dlc",
}

RU_EXCLUDED_SUFFIXES = {
    "vk.ru",
    "vk.com",
    "vkvideo.ru",
    "vkuser.net",
    "vkuservideo.net",
    "mycdn.me",
    "mail.ru",
    "inbox.ru",
    "list.ru",
    "bk.ru",
    "ok.ru",
    "odnoklassniki.ru",
    "yandex.ru",
    "yandex.net",
    "ya.ru",
    "dzen.ru",
    "rutube.ru",
    "rambler.ru",
    "kinoafisha.info",
    "cdn-vk.ru",
}

RU_TLDS = (".ru", ".su", ".xn--p1ai")

ADS_EXCLUDED_DOMAINS = {
    "yabs.yandex.ru",
}


def load_apple_direct_domains() -> list[str]:
    """Load apple direct domains from sources/apple.txt"""
    return load_domain_file(APPLE_DIRECT_FILE, normalize_text_domain)


def load_category_ru_direct_domains() -> list[str]:
    """Load category-ru direct domains from sources/category-ru-direct.txt"""
    return load_domain_file(CATEGORY_RU_DIRECT_FILE, normalize_text_domain)


def fetch_text(url: str, *, timeout: int = 90) -> str:
    """Fetch text content from URL with automatic retry on transient errors."""
    resp = SESSION.get(url, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def fetch_lines(url: str) -> list[str]:
    return fetch_text(url).splitlines()


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


def write_tag(tag: str, lines: list[str]) -> None:
    path = DATA_DIR / tag
    content = "\n".join(lines).strip() + "\n"
    path.write_text(content, encoding="utf-8")


def cleanup_data_dir() -> None:
    for item in DATA_DIR.iterdir():
        if item.is_dir():
            shutil.rmtree(item)
        else:
            item.unlink()


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
    return required_attrs.issubset(rule_attrs)


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
    except requests.RequestException as e:
        print(f"Warning: skip missing DLC include: {tag} ({e})")
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

    return domain.endswith(RU_TLDS)


def build_ads() -> None:
    domains: set[str] = set()

    # DLC category-ads-all
    for rule in flatten_rules("category-ads-all"):
        rule = rule.strip()
        if not rule or rule.startswith(("full:", "keyword:", "regexp:", "domain:", "include:")):
            continue
        domain = normalize_text_domain(rule)
        if domain and domain not in ADS_EXCLUDED_DOMAINS:
            domains.add(domain)

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
        except requests.RequestException as e:
            print(f"Warning: Failed to fetch HaGeZi Light list from {url}: {e}")

    if not hagezi_fetched:
        print("Warning: All HaGeZi Light mirrors failed")

    # Peter Lowe
    try:
        for line in fetch_text(PETER_LOWE_URL).splitlines():
            domain = normalize_text_domain(line)
            if domain and domain not in ADS_EXCLUDED_DOMAINS:
                domains.add(domain)
    except requests.RequestException as e:
        print(f"Warning: Failed to fetch Peter Lowe list from {PETER_LOWE_URL}: {e}")

    if not domains:
        raise RuntimeError("category-ads-all is empty")

    print(f"ADS total: {len(domains)}")
    write_tag("category-ads-all", sorted(domains))


def build_ru_blocked() -> None:
    """Build ru-blocked from legacy upstream sources plus manual domains."""
    domains: set[str] = set()

    try:
        for line in fetch_lines(ANTIFILTER_RU_BLOCKED_URL):
            domain = normalize_text_domain(line)
            if domain:
                domains.add(domain)
    except requests.RequestException as e:
        print(f"Warning: Failed to fetch antifilter list from {ANTIFILTER_RU_BLOCKED_URL}: {e}")

    category_ru_domains = extract_plain_domains_from_rules(flatten_rules("category-ru"))

    try:
        for line in fetch_lines(PROXY_URL):
            domain = normalize_text_domain(line)
            if not domain or domain in category_ru_domains or is_ru_excluded_domain(domain):
                continue
            domains.add(domain)
    except requests.RequestException as e:
        print(f"Warning: Failed to fetch proxy list from {PROXY_URL}: {e}")

    for domain in load_domain_file(MANUAL_RU_BLOCKED_FILE, normalize_text_domain):
        domains.add(domain)

    write_tag("ru-blocked", sorted(domains))
    print(f"RU blocked total: {len(domains)}")


def build_flat_root_tags() -> None:
    for tag in ROOT_TAGS:
        if tag == "category-ads-all":
            continue

        print(f"Building tag: {tag}")

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


def main() -> None:
    cleanup_data_dir()
    build_ru_blocked()
    build_ads()
    build_flat_root_tags()
    print("Done.")


if __name__ == "__main__":
    main()
