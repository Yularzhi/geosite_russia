from pathlib import Path
from urllib.parse import urlparse
import re
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Текстовые внешние списки, которые мы сами объединяем в custom-ru
TEXT_SOURCES = {
    "custom-ru": [
        "https://community.antifilter.download/list/domains.txt",
        "https://raw.githubusercontent.com/1andrevich/Re-filter-lists/main/domains_all.lst",
    ],
}

# Теги, которые подтягиваем из upstream domain-list-community
# ВЫХОДНОЕ ИМЯ -> ИСХОДНЫЙ TAG В DLC
DLC_TAGS = {
    "category-ads": "category-ads-all",
    "telegram": "telegram",
    "viber": "viber",
    "whatsapp": "whatsapp",
    "meta": "meta",
    "facebook": "facebook",
    "google": "google",
    "supercell": "supercell",
    "roblox": "roblox",
}

DLC_BASE = "https://raw.githubusercontent.com/v2fly/domain-list-community/master/data/"

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "custom-geosite-builder/1.0",
    }
)

DOMAIN_RE = re.compile(r"^(?:[a-z0-9-]+\.)+[a-z]{2,63}$")
SEEN_DLC_TAGS: dict[str, set[str]] = {}


def fetch_text(url: str) -> str:
    resp = SESSION.get(url, timeout=90)
    resp.raise_for_status()
    return resp.text


def fetch_lines(url: str) -> list[str]:
    return fetch_text(url).splitlines()


def normalize_text_domain(line: str) -> str | None:
    """
    Нормализация обычных текстовых списков:
    - community.antifilter.download
    - Re-filter-lists
    """
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

    # если вдруг попадется dlc-like формат
    for prefix in ("full:", "domain:", "keyword:", "regexp:"):
        if line.startswith(prefix):
            line = line[len(prefix):].strip()

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

    # удаляем :port
    if ":" in line and line.count(":") == 1:
        host, port = line.split(":", 1)
        if port.isdigit():
            line = host

    if not line:
        return None
    if "_" in line:
        return None
    if line.endswith(".local"):
        return None

    return line if DOMAIN_RE.match(line) else None


def parse_dlc_line(line: str) -> str | None:
    """
    Преобразует строки из domain-list-community в нормальный вид
    для нашего кастомного data/<tag>.
    """

    line = line.strip()

    if not line:
        return None
    if line.startswith("#"):
        return None

    # убираем inline-комментарии: "include:apple-dev # swift inside"
    if "#" in line:
        line = line.split("#", 1)[0].strip()

    if not line:
        return None

    # убираем атрибуты вида: @ads
    if " @" in line:
        line = line.split(" @", 1)[0].strip()

    if not line:
        return None

    # include сохраняем как есть
    if line.startswith("include:"):
        include_tag = line.split(":", 1)[1].strip()
        if include_tag:
            return f"include:{include_tag}"
        return None

    for prefix in ("full:", "domain:", "keyword:", "regexp:"):
        if line.startswith(prefix):
            value = line[len(prefix):].strip()
            if value:
                return f"{prefix}{value}"
            return None

    # обычный домен
    plain = line.strip().lower().strip(".")
    if plain.startswith("*."):
        plain = plain[2:]
    if plain.startswith("."):
        plain = plain[1:]

    return plain if plain else None


def fetch_dlc_tag(tag: str, seen: set[str] | None = None) -> set[str]:
    """
    Рекурсивно подтягивает tag из domain-list-community.
    include:* разворачиваем, чтобы итоговые файлы были самодостаточными.
    """
    if tag in SEEN_DLC_TAGS:
        return set(SEEN_DLC_TAGS[tag])

    if seen is None:
        seen = set()
    if tag in seen:
        return set()

    seen.add(tag)

    url = DLC_BASE + tag
    try:
        lines = fetch_lines(url)
    except requests.HTTPError as e:
        print(f"[WARN] failed to fetch DLC tag '{tag}': {e}")
        return set()

    result: set[str] = set()

    for raw in lines:
        parsed = parse_dlc_line(raw)
        if not parsed:
            continue

        if parsed.startswith("include:"):
            child = parsed.split(":", 1)[1].strip()
            if child:
                result.update(fetch_dlc_tag(child, seen))
        else:
            result.add(parsed)

    SEEN_DLC_TAGS[tag] = set(result)
    return result


def write_tag(tag: str, entries: set[str]) -> None:
    target = DATA_DIR / tag
    content = "\n".join(sorted(entries)) + "\n"
    target.write_text(content, encoding="utf-8")


def cleanup_data_dir() -> None:
    if DATA_DIR.exists():
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

    write_tag("custom-ru", domains)


def build_dlc_tags() -> None:
    for output_tag, source_tag in DLC_TAGS.items():
        entries = fetch_dlc_tag(source_tag)
        write_tag(output_tag, entries)


def main() -> None:
    cleanup_data_dir()
    build_custom_ru()
    build_dlc_tags()

    print("Done. Generated tags:")
    for file in sorted(DATA_DIR.iterdir()):
        if file.is_file():
            print(f"- {file.name}")


if __name__ == "__main__":
    main()
