"""Integrate an owner-submitted AI Discover issue into the public edition."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys

from validate_snapshots import discoveries, discovery_key, require, validate, validate_discoveries

TITLE_PREFIX = "AI Discover candidate — "
FIELDS = {"url", "title", "source", "date", "summary", "periods", "type", "interests", "image", "imageRights"}


def integrate(previous, submission, stamp):
    require(isinstance(submission, dict) and set(submission) == {"preferenceMode", "items"},
            "Expected a JSON object with preferenceMode and items")
    mode = submission["preferenceMode"]
    require(mode in ("latest", "previous", "baseline"), "Invalid preferenceMode")
    items = submission["items"]
    require(isinstance(items, list) and 0 < len(items) <= 10, "Provide between 1 and 10 articles")
    seen = set(discoveries(previous))
    additions = []
    for item in items:
        require(isinstance(item, dict) and set(item) <= FIELDS, "Unexpected candidate article field")
        key = discovery_key(item["url"])
        if key not in seen:
            seen.add(key)
            additions.append({**item, "discoveredAt": stamp})
    if not additions:
        return previous, 0, mode
    ordered = sorted(additions + previous["items"],
                     key=lambda item: (item.get("discoveredAt") or "", item.get("date") or ""),
                     reverse=True)
    kept, retired = ordered[:40], ordered[40:]
    history = dict(previous.get("discoveryHistory", {}))
    archived = {discovery_key(url) for url in history}
    for item in retired:
        if discovery_key(item["url"]) not in archived:
            history[item["url"]] = item["discoveredAt"]
    result = {**previous, "updated": stamp, "items": kept, "discoveryHistory": history}
    validate(result, "AI Discover")
    validate_discoveries(result, previous)
    return result, len(additions), mode


def main():
    issue_path, owner, edition_path, output_path = sys.argv[1:]
    issue = json.loads(Path(issue_path).read_text(encoding="utf-8"))
    require(issue["author"]["login"] == owner, "Candidate issue is not from the repository owner")
    require(issue["state"] == "OPEN" and issue["title"].startswith(TITLE_PREFIX), "Candidate issue is not open")
    body = issue["body"].strip()
    require(len(body) <= 30000, "Candidate JSON is too large")
    path = Path(edition_path)
    previous = json.loads(path.read_text(encoding="utf-8"))
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    result, count, mode = integrate(previous, json.loads(body), stamp)
    if count:
        path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    with Path(output_path).open("a", encoding="utf-8") as outputs:
        outputs.write(f"added={count}\ntotal={len(result['items'])}\nmode={mode}\n")


if __name__ == "__main__":
    main()
