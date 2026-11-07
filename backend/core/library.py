import re
from pathlib import Path
from .schemas import LibraryItem
from .config import settings

def _parse_header(block: str) -> dict:
    data = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, _, val = line.partition(":")
        val = re.split(r"\s+#\s", val.strip())[0].strip()   # drop inline comments
        data[key.strip()] = val
    return data

def load_item(path: Path) -> LibraryItem:
    text = path.read_text(encoding="utf-8")
    head, body = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S).groups()
    h = _parse_header(head)
    sections = {m.group(1): m.group(2).strip()
                for m in re.finditer(r"^## (.+?)\n(.*?)(?=^## |\Z)", body, re.S | re.M)}
    def sect(prefix):
        return next((v for k, v in sections.items() if k.startswith(prefix)), "")
    h["applies_to"] = [a.strip() for a in h["applies_to"].strip("[]").split(",")]
    excerpt = [l for l in sect("Excerpt").splitlines() if l.strip()]
    return LibraryItem(**{k: v for k, v in h.items() if k in LibraryItem.model_fields},
                       excerpt=excerpt, meaning=sect("Plain-language"), limits=sect("Limits"))

def load_library(verified_only: bool = False) -> dict[str, LibraryItem]:
    items = {}
    for p in sorted(settings.library_dir.rglob("*.md")):
        if p.name.startswith("INDEX"):
            continue
        item = load_item(p)
        assert item.id not in items, f"duplicate id {item.id}"
        if item.is_verified or not verified_only:
            items[item.id] = item
    return items