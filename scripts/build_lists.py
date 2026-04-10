from pathlib import Path
from urllib.parse import urlparse
import re
import requests

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

SESSION = requests.Session()
SESSION.headers.update(
    {
        "User-Agent": "custom-geosite-builder/1.0",
    }
)

DOMAIN_RE = re.compile(r"^(?:[a-z0-9-]+\.)+[a-z]{2,63}$")

# Источники для custom-ru
TEXT_SOURCES = {
    "custom-ru": [
        "https://community.antifilter.download/list/domains.txt",
        "https://raw.githubusercontent.com/1andrevich/Re-filter-lists/main/domains_all.lst",
    ],
}

# Какие upstream-файлы из domain-list-community нужно просто копировать как есть
RAW_DLC_TAGS = {
    "category-ads-all": "category-ads-all",
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

    if not line:
        return None
    if "_" in line:
        return None
    if line.endswith(".local"):
        return None

    return line if DOMAIN_RE.match(line) else None


def write_tag(tag: str, content: str) -> None:
    target = DATA_DIR / tag
    if not content.endswith("\n"):
        content += "\n"
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

    content = "\n".join(sorted(domains)) + "\n"
    write_tag("custom-ru", content)


def build_raw_dlc_tags() -> None:
    for output_tag, source_tag in RAW_DLC_TAGS.items():
        url = DLC_BASE + source_tag
        content = fetch_text(url)
        write_tag(output_tag, content)


def main() -> None:
    cleanup_data_dir()
    build_custom_ru()
    build_raw_dlc_tags()

    print("Done. Generated tags:")
    for file in sorted(DATA_DIR.iterdir()):
        if file.is_file():
            print(f"- {file.name}")


if __name__ == "__main__":
    main()
