"""Validate publishable feed and editorial snapshots."""
from datetime import date, datetime
import json
from urllib.parse import urlsplit

from refresh import ROOT, canonical


def require(condition, message):
    if not condition:
        raise ValueError(message)


def read(path):
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def validate(edition, name, sources=None):
    updated = datetime.fromisoformat(edition["updated"].replace("Z", "+00:00"))
    items = edition["items"]
    require(isinstance(items, list) and items, f"{name}: no items")
    seen = set()
    ids = set()
    for item in items:
        url = item["url"]
        normalized = canonical(url)
        parts = urlsplit(url)
        require(normalized and not parts.username, f"{name}: invalid URL {url}")
        key = normalized.split("://", 1)[1]
        require(key not in seen, f"{name}: duplicate URL {url}")
        seen.add(key)
        for field in ("title", "summary", "source", "type"):
            require(isinstance(item[field], str) and item[field].strip(), f"{name}: missing {field} for {url}")
        for field in ("periods", "interests"):
            require(isinstance(item[field], list) and all(isinstance(value, str) for value in item[field]),
                    f"{name}: invalid {field} for {url}")
        if sources is not None:
            require(item["source"] in sources, f"{name}: unknown source for {url}")
            require(item["id"] and item["id"] not in ids, f"{name}: duplicate or empty item ID for {url}")
            ids.add(item["id"])
            datetime.fromisoformat(item["date"].replace("Z", "+00:00"))
        else:
            require(parts.scheme == "https", f"{name}: non-HTTPS article URL {url}")
            if item.get("date"):
                date.fromisoformat(item["date"])
            if item.get("image"):
                rights = item.get("imageRights", {})
                require(rights.get("credit") and rights.get("license") and rights.get("licenseUrl"),
                        f"{name}: image attribution is incomplete for {url}")
    print(f"{name}: validated {len(items)} items (updated {updated.isoformat()})")


def main():
    feed = read("docs/assets/feed.json")
    expected_sources = {source["id"] for source in read("sources.json")}
    feed_sources = {source["id"] for source in feed["sources"]}
    require(feed_sources == expected_sources, "Regular feed sources do not match the approved registry")
    validate(feed, "Regular feed", feed_sources)
    validate(read("docs/assets/ai-discover.json"), "AI Discover")


if __name__ == "__main__":
    main()
