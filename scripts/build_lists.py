from pathlib import Path
from urllib.parse import urlparse
import re
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
SOURCES_DIR = ROOT / "sources"

DATA_DIR.mkdir(parents=True, exist_ok=True)
SOURCES_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "custom-geosite-builder/1.0"})

DOMAIN_RE = re.compile(r"^(?:[a-z0-9-]+\.)+[a-z]{2,63}$")

DLC_BASE = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"
PROXY_URL = "https://raw.githubusercontent.com/Loyalsoldier/surge-rules/release/proxy.txt"
MANUAL_RU_BLOCKED_FILE = SOURCES_DIR / "manual_ru_blocked.txt"

TEXT_SOURCES = {
    "ru-blocked": [
        "https://community.antifilter.download/list/domains.txt",
    ],
}

ROOT_TAGS = [
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

ROOT_TAG_SOURCE = {
    "category-ads-all": "dlc",
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

# Явно российские домены/суффиксы, которые не должны попадать в ru-blocked
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

# Дополнительные домены для viber
VIBER_EXTRA_DOMAINS = [
    "api.viber.com",
    "invite.viber.com",
    "ads.viber.com",
    "market.viber.com",
    "share.viber.com",
    "unv.viber.com",
    "pg-vb.cdn.viber.com",
    "vbr.com",
    "abff.viber.com",
    "explore.api.viber.com",
    "abtest.api.viber.com",
]

# Дополнительные домены для apple
APPLE_DIRECT_DOMAINS = [
    "apps.apple.com",
    "itunes.apple.com",
    "mzstatic.com",
    "cdn-apple.com",
    "apple-dns.net",
    "aaplimg.com",
    "ls.apple.com",
    "gspe1-ssl.ls.apple.com",
    "akadns.net",
    "akamai.net",
    "akamaiedge.net",
    "edgekey.net",
    "edgesuite.net",
]

def fetch_text(url: str) -> str:
    resp = SESSION.get(url, timeout=90)
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

    # antifilter format: *://*.example.com/*
    line = line.replace("*://*.", "")
    line = line.replace("*://", "")
    line = line.replace("/*", "")
    line = line.replace("/", "")

    line = line.replace("\t", " ").split(" ")[0].strip()

    if line.startswith("http://") or line.startswith("https://"):
        parsed = urlparse(line)
        line = parsed.hostname or ""

    line = line.strip().strip(".")
    if line.startswith("*."):
        line = line[2:]
    if line.startswith("."):
        line = line[1:]

    line = line.split("/")[0]

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
        if item.is_file():
            item.unlink()


def strip_inline_comment(line: str) -> str:
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.strip()


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

    text = fetch_text(get_tag_url(tag))
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

    if domain.endswith(RU_TLDS):
        return True

    return False


def load_manual_domains(file_path: Path) -> list[str]:
    if not file_path.exists():
        return []

    domains: list[str] = []
    for raw_line in file_path.read_text(encoding="utf-8").splitlines():
        line = strip_inline_comment(raw_line)
        if not line:
            continue
        domains.append(line)

    return domains


def build_ru_blocked() -> None:
    domains: set[str] = set()

    # antifilter
    for url in TEXT_SOURCES["ru-blocked"]:
        for line in fetch_lines(url):
            domain = normalize_text_domain(line)
            if domain:
                domains.add(domain)

    # category-ru plain domains for exclusion from proxy.txt
    category_ru_rules = flatten_rules("category-ru")
    category_ru_domains = extract_plain_domains_from_rules(category_ru_rules)

    # proxy.txt minus category-ru and minus explicit RU exclusions
    for line in fetch_lines(PROXY_URL):
        domain = normalize_text_domain(line)
        if not domain:
            continue
        if domain in category_ru_domains:
            continue
        if is_ru_excluded_domain(domain):
            continue
        domains.add(domain)

    # manual additions from file
    for domain in load_manual_domains(MANUAL_RU_BLOCKED_FILE):
        normalized = normalize_text_domain(domain)
        if normalized:
            domains.add(normalized)

    write_tag("ru-blocked", sorted(domains))


def build_flat_root_tags() -> None:
    for tag in ROOT_TAGS:
        print(f"Building tag: {tag}")

        if tag == "viber":
            rules = flatten_rules("viber")
            rules.extend(flatten_rules("rakuten"))
            rules.extend(VIBER_EXTRA_DOMAINS)
        elif tag == "apple":
            rules = APPLE_DIRECT_DOMAINS    
        else:
            rules = flatten_rules(tag)

        rules = dedupe_keep_order(rules)
        write_tag(tag, rules)


def main() -> None:
    cleanup_data_dir()
    build_ru_blocked()
    build_flat_root_tags()
    print("Done.")


if __name__ == "__main__":
    main()