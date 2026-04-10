from pathlib import Path
from urllib.parse import urlparse
import re
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "custom-geosite-builder/1.0"})

DOMAIN_RE = re.compile(r"^(?:[a-z0-9-]+\.)+[a-z]{2,63}$")

DLC_BASE = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"
RUNETFREEDOM_BASE = "https://raw.githubusercontent.com/runetfreedom/russia-domains-list/main/"

TEXT_SOURCES = {
    "custom-ru": [
        "https://community.antifilter.download/list/domains.txt",
        "https://raw.githubusercontent.com/1andrevich/Re-filter-lists/main/domains_all.lst",
    ],
}

# Только эти теги должны попасть в итоговый geosite.dat как отдельные секции
ROOT_TAGS = [
    "category-ads-all",
    "telegram",
    "viber",
    "whatsapp",
    "meta",
    "facebook",
    "google",
    "supercell",
    "roblox",
    "private",
    "ru-available-only-inside",
]

# Явно указываем только особые корневые теги.
# Все include-зависимости по умолчанию считаем тегами из domain-list-community.
ROOT_TAG_SOURCE = {
    "category-ads-all": "dlc",
    "telegram": "dlc",
    "viber": "dlc",
    "whatsapp": "dlc",
    "meta": "dlc",
    "facebook": "dlc",
    "google": "dlc",
    "supercell": "dlc",
    "roblox": "dlc",
    "private": "dlc",
    "ru-available-only-inside": "runetfreedom",
}


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


def write_tag(tag: str, content: str) -> None:
    path = DATA_DIR / tag
    if not content.endswith("\n"):
        content += "\n"
    path.write_text(content, encoding="utf-8")


def cleanup_data_dir() -> None:
    for item in DATA_DIR.iterdir():
        if item.is_file():
            item.unlink()


def build_custom_ru() -> None:
    domains: set[str] = set()

    for url in TEXT_SOURCES["custom-ru"]:
        for line in fetch_lines(url):
            domain = normalize_text_domain(line)
            if domain:
                domains.add(domain)

    write_tag("custom-ru", "\n".join(sorted(domains)) + "\n")


def get_tag_url(tag: str) -> str:
    source = ROOT_TAG_SOURCE.get(tag, "dlc")

    if source == "dlc":
        return DLC_BASE + tag
    if source == "runetfreedom":
        return RUNETFREEDOM_BASE + tag

    raise ValueError(f"Unknown source for tag: {tag}")


def strip_inline_comment(line: str) -> str:
    if "#" in line:
        line = line.split("#", 1)[0]
    return line.strip()


def parse_upstream_line(line: str) -> tuple[str, str] | None:
    """
    Возвращает:
    - ("include", "child-tag")
    - ("rule", "raw rule line")
    - None
    """
    line = strip_inline_comment(line)
    if not line:
        return None

    if line.startswith("include:"):
        child = line.split(":", 1)[1].strip()
        # include:acfun @ads  -> acfun
        child = child.split()[0] if child else ""
        if child:
            return ("include", child)
        return None

    # Сохраняем правило как есть:
    # domain
    # full:domain
    # keyword:...
    # regexp:...
    # domain @attr
    return ("rule", line)


def flatten_tag(tag: str, seen: set[str] | None = None) -> list[str]:
    if seen is None:
        seen = set()

    if tag in seen:
        return []

    seen.add(tag)

    text = fetch_text(get_tag_url(tag))
    rules: list[str] = []

    for raw_line in text.splitlines():
        parsed = parse_upstream_line(raw_line)
        if not parsed:
            continue

        kind, value = parsed

        if kind == "include":
            rules.extend(flatten_tag(value, seen))
        else:
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


def build_flattened_root_tags() -> None:
    for tag in ROOT_TAGS:
        rules = flatten_tag(tag)
        rules = dedupe_keep_order(rules)
        write_tag(tag, "\n".join(rules) + "\n")


def main() -> None:
    cleanup_data_dir()
    build_custom_ru()
    build_flattened_root_tags()

    print("Done. Generated tags:")
    for file in sorted(DATA_DIR.iterdir()):
        if file.is_file():
            print(f"- {file.name}")


if __name__ == "__main__":
    main()
