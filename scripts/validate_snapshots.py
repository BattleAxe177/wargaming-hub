"""Validate publishable feed and editorial snapshots."""
import argparse
from datetime import date, datetime
from pathlib import Path
import re
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


def discovery_time(value):
    require(isinstance(value, str) and re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value),
            f"AI Discover: invalid discovery timestamp {value!r}")
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def discovery_key(url):
    normalized = canonical(url)
    require(normalized and not urlsplit(url).username, f"AI Discover: invalid discovery URL {url}")
    return normalized.split("://", 1)[1]


def discoveries(edition):
    dates = {}
    for url, stamp in edition.get("discoveryHistory", {}).items():
        key = discovery_key(url)
        require(key not in dates, f"AI Discover: duplicate archived URL {url}")
        if stamp is not None:
            discovery_time(stamp)
        dates[key] = stamp
    for item in edition["items"]:
        key = discovery_key(item["url"])
        require("discoveredAt" in item, f"AI Discover: missing discoveredAt for {item['url']}")
        stamp = item.get("discoveredAt")
        if stamp is not None:
            discovery_time(stamp)
        require(key not in dates or dates[key] == stamp, f"AI Discover: inconsistent discovery history for {key}")
        dates[key] = stamp
    return dates


def validate_discoveries(edition, previous=None):
    current = discoveries(edition)
    updated = edition["updated"]
    cutoff = updated if len(updated) > 10 else updated + "T23:59:59Z"
    limit = discovery_time(cutoff)
    require(all(stamp is None or discovery_time(stamp) <= limit for stamp in current.values()),
            "AI Discover: discovery is later than the edition")
    if previous is None:
        return
    before = discoveries(previous)
    prior_edition = previous["updated"]
    prior_cutoff = prior_edition if len(prior_edition) > 10 else prior_edition + "T00:00:00Z"
    latest = max([prior_cutoff, *(stamp for stamp in before.values() if stamp is not None)])
    for key, stamp in before.items():
        require(key in current, f"AI Discover: preserve retired discovery in discoveryHistory: {key}")
        require(current[key] == stamp, f"AI Discover: discovery timestamp changed for {key}")
    active = {discovery_key(item["url"]) for item in edition["items"]}
    for key in current.keys() - before.keys():
        require(key in active and current[key] == updated and updated > latest,
                f"AI Discover: newly added URL must be stamped with the new edition's UTC time: {key}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--previous", type=Path, help="Existing main-branch AI Discover snapshot")
    args = parser.parse_args()
    feed = read("docs/assets/feed.json")
    expected_sources = {source["id"] for source in read("sources.json")}
    feed_sources = {source["id"] for source in feed["sources"]}
    require(feed_sources == expected_sources, "Regular feed sources do not match the approved registry")
    validate(feed, "Regular feed", feed_sources)
    edition = read("docs/assets/ai-discover.json")
    validate(edition, "AI Discover")
    previous = json.loads(args.previous.read_text(encoding="utf-8")) if args.previous else None
    validate_discoveries(edition, previous)


if __name__ == "__main__":
    main()
