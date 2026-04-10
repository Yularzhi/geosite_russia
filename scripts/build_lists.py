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

TEXT_SOURCES = {
    "custom-ru": [
        "https://community.antifilter.download/list/domains.txt",
        "https://raw.githubusercontent.com/1andrevich/Re-filter-lists/main/domains_all.lst",
    ],
}

ROOT_DLC_TAGS = [
    "category-ads-all",
    "telegram",
    "viber",
    "whatsapp",
    "meta",
    "facebook",
    "google",
    "supercell",
    "roblox",
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


def extract_includes(text: str) -> set[str]:
    includes: set[str] = set()

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        # убираем inline комментарий
        if "#" in line:
            line = line.split("#", 1)[0].strip()

        if not line:
            continue

        # domain-list-community часто хранит много токенов в одной строке
        for token in line.split():
            if token.startswith("include:"):
                child = token.split(":", 1)[1].strip()
                if child:
                    includes.add(child)

    return includes


def fetch_dlc_with_dependencies(root_tags: list[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    queue = list(root_tags)
    seen: set[str] = set()

    while queue:
        tag = queue.pop(0)
        if tag in seen:
            continue
        seen.add(tag)

        text = fetch_text(DLC_BASE + tag)
        result[tag] = text

        for child in sorted(extract_includes(text)):
            if child not in seen:
                queue.append(child)

    return result


def build_dlc_tags() -> None:
    dlc_files = fetch_dlc_with_dependencies(ROOT_DLC_TAGS)
    for tag, content in dlc_files.items():
        write_tag(tag, content)


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
