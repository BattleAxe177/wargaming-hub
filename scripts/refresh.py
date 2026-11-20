"""Collect public RSS/Atom entries and retain the last good copy of each item."""
import concurrent.futures
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import parse_qsl, urlencode, urljoin, urlsplit, urlunsplit
from urllib.request import Request, urlopen
from xml.etree import ElementTree

ROOT = Path(__file__).resolve().parents[1]
PERIODS = {
    "Ancients": r"roman|punic|ancient|hoplite|carthag|diadoch|alexander the great",
    "Medieval": r"medieval|viking|crusad|hastings|agincourt|hundred years|war[s]? of the roses|norman conquest|teutonic|samurai|sengoku",
    "Renaissance": r"renaissance|italian wars|pavia|bicocca|landsknecht|cerignola|pike and shot|thirty years|english civil war|ecw|edgehill|marston moor",
    "18th Century": r"seven years|american revolution|american war of independence|aw[i]|jacobite|french and indian|trenton|frederick the great|marlborough|spanish succession|syw",
    "Napoleonic": r"napoleon|waterloo|borodino|austerlitz|peninsular war|quatre bras|wagram",
    "American Civil War": r"american civil war|acw|gettysburg|confederate|antietam|shiloh|secession",
    "19th Century": r"colonial|zulu|crimea|sudan|franco.prussian|boer war|mahdist|victorian",
    "World War I": r"world war i\b|ww1|wwi\b|great war|gallipoli|verdun",
    "Interwar": r"interwar|spanish civil war|chaco war",
    "World War II": r"world war (ii|2)|ww2|wwii|normandy|barbarossa|stalingrad|194[0-5]|chain of command|afrika korps|tank on tank|bir kalifa",
    "Modern": r"cold war|vietnam|korean war|falklands|modern warfare|gulf war|postwar|opfor|krasnovia"
}
KINDS = {
    "Battle report": r"aar\b|batrep|battle report|game report|playtest|played|game turns|turn one|turn 1|refight",
    "Painting & modeling": r"paint|brush|basing|rebasing|sculpt|terrain build|3d print|miniatures completed|painting desk",
    "Scenario & rules": r"scenario|campaign rules|ruleset|rules review|rulebook|rules draft",
    "Hobby news": r"release|newsletter|show report|convention|announcement|convention|sale",
}
MEDIA = "{http://search.yahoo.com/mrss/}"

class PlainText(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []
        self.images = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style"}:
            self.hidden += 1

        if tag == "img" and not self.hidden:
            attrs = dict(attrs)
            if any(value in {"0", "1", "2"} for value in (attrs.get("width"), attrs.get("height"))):
                return
            url = attrs.get("data-src") or attrs.get("src")
            if url:
                self.images.append(url)

    def handle_endtag(self, tag):
        if tag in {"script", "style"} and self.hidden:
            self.hidden -= 1

    def handle_data(self, data):
        if not self.hidden:
            self.parts.append(data)


def plain(html):
    parser = PlainText()
    parser.feed(html)
    return " ".join(" ".join(parser.parts).split())


def article_image(entry, html, article_url):
    parser = PlainText()
    parser.feed(html)
    thumbnails = [element.get("url") for element in entry.iter(MEDIA + "thumbnail")]
    for candidate in parser.images + thumbnails:
        if not candidate:
            continue
        url = urljoin(article_url, candidate.strip())
        parts = urlsplit(url)
        if (parts.scheme == "https" and parts.hostname and not parts.username
                and not re.search(r"avatar|emoji|smiley|tracking|pixel|feeds\.feedburner", url, re.I)):
            return url
    return ""


def canonical(url):
    parts = urlsplit(url.strip())
    if parts.scheme not in {"http", "https"} or not parts.hostname:
        return ""
    query = sorted((k, v) for k, v in parse_qsl(parts.query, keep_blank_values=True)
                   if not k.lower().startswith("utm_") and k.lower() not in {"fbclid", "gclid", "m"})
    return urlunsplit((parts.scheme, parts.netloc.lower(), parts.path.rstrip("/") or "/", urlencode(query), ""))


def matching(text, patterns):
    return [label for label, pattern in patterns.items() if re.search(r"\b(?:" + pattern + r")", text, re.I)]


def collect(source, stamp):
    request = Request(source["feed"], headers={"User-Agent": "WargamingHub/1.0 (public RSS reader)"})
    with urlopen(request, timeout=20) as response:
        raw = response.read(5_000_001)
    if len(raw) > 5_000_000:
        raise ValueError("feed exceeds size limit")
    root = ElementTree.fromstring(raw)
    entries = root.findall("{*}entry") + root.findall("./{*}channel/{*}item")
    include = re.compile(source["include"], re.I) if source.get("include") else None
    exclude = re.compile(source["exclude"], re.I) if source.get("exclude") else None
    items = []
    for entry in entries[:40]:
        def field(*names):
            for name in names:
                value = entry.findtext("{*}" + name)
                if value:
                    return value
            return ""

        title = plain(field("title"))
        links = entry.findall("{*}link")
        url = next((canonical(link.get("href") or link.text or "") for link in links
                    if link.get("rel", "alternate") == "alternate"), "")
        date = field("published", "pubDate", "date", "updated")
        try:
            date = datetime.fromisoformat(date.replace("Z", "+00:00"))
        except ValueError:
            try:
                date = parsedate_to_datetime(date)
            except (ValueError, TypeError):
                continue
        date = date.replace(tzinfo=date.tzinfo or timezone.utc).astimezone(timezone.utc)
        if not (url and title) or date > stamp + timedelta(hours=12):
            continue
        labels = " ".join(c.get("term") or c.text or "" for c in entry.findall("{*}category"))
        heading = f"{title} {labels}"
        if (include and not include.search(heading)) or (exclude and exclude.search(heading)):
            continue
        article_html = field("content", "encoded", "description", "summary")
        video_description = entry.findtext(f"{MEDIA}group/{MEDIA}description", "")
        body = plain(article_html or video_description)
        image = article_image(entry, article_html, url) if source["kind"] != "Forum" else ""
        periods = matching(f"{title} {labels}", PERIODS) or matching(body[:650], PERIODS)
        kinds = matching(title, KINDS) or matching(labels, KINDS) or matching(body[:500], KINDS)
        kind = kinds[0] if kinds else source.get("type", "Hobby journal")
        topic = f"{title} {labels} {body[:900]}"
        interests = [
            label for label, pattern in {
                "Small tables": r"small.table|small.board|compact|portable wargame|coffee.table",
                "Small scale": r"\b(?:2|3|6|10)\s*mm\b",
                "Scenario design": r"scenario|battlefield map",
                "Italian Wars": r"italian wars|bicocca|pavia|novara|cerignola",
                "Normandy": r"normandy|mortain|falaise|operation cobra",
                "Seven Days": r"seven days|glendale|malvern hill|mechanicsville",
                "Fast play": r"fast.play|quick.play|one.hour",
            }.items() if re.search(pattern, topic, re.I)
        ]
        # Use a short descriptive summary instead of republishing the source text.
        editorial = source.get("editorial", {}).get(title, {})
        periods = editorial.get("periods", periods)
        kind = editorial.get("type", kind)
        summary = editorial.get("summary")
        if not summary:
            verb = {"Battle report": "A tabletop game report", "Painting & modeling": "A hobby bench update",
                    "Scenario & rules": "A post on tabletop scenarios or rules", "Hobby news": "A hobby news update",
                    "Forum discussion": "A public community discussion"}.get(kind, "A hobby journal entry")
            if source["kind"] == "YouTube":
                verb = "A tabletop wargaming video"
            subject = " covering " + " and ".join(periods[:2]) if periods else ""
            summary = f"{verb}{subject} from {source['name']}."
            if labels and source["kind"] != "Forum":
                topics = list(dict.fromkeys(c.get("term") or c.text or "" for c in entry.findall("{*}category")))
                topics = [plain(t) for t in topics if t and len(t) <= 48][:3]
                if topics:
                    summary += " Filed under " + ", ".join(topics) + "."
            if interests:
                summary += " Topics include " + ", ".join(t.lower() for t in interests) + "."
        identifier = url
        if source["id"] == "pendraken":
            match = re.search(r"(/index\.php/topic,\d+)(?:\.|/|$)", url)
            if not match:
                continue
            identifier = f"https://www.pendrakenforum.co.uk{match[1]}.0.html"
            title = re.sub(r"^Re:\s*", "", title, flags=re.I)
            if re.fullmatch(r"\d{4} Games Count|Deaths in \d{4}|Zombicide\?", title, re.I):
                continue
            summary = source.get("editorial", {}).get(title, {}).get("summary") or (
                "Public Pendraken Forum thread about " + title.rstrip(".!?") + "."
            )
            kind = "Forum discussion"
        items.append(dict(id=identifier, url=url, title=title, source=source["id"], summary=summary,
                          date=date.isoformat(), periods=periods or ["Mixed & general"], type=kind,
                          interests=interests, image=image, featured=editorial.get("featured", False),
                          discovered=stamp.isoformat()))
    return items


def main():
    stamp = datetime.now(timezone.utc).replace(microsecond=0)
    sources = json.loads((ROOT / "sources.json").read_text())
    path = ROOT / "docs/assets/feed.json"
    prior = json.loads(path.read_text()) if path.exists() else {}
    records = {item["id"]: item for item in prior.get("items", [])}
    names = {source["id"] for source in sources}
    records = {key: item for key, item in records.items() if item["source"] in names and
               not (item["source"] == "pendraken" and key != re.sub(r"\.msg\d+\.html$", ".0.html", key))}
    failures = []
    seen = set()
    successes = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = [pool.submit(collect, source, stamp) for source in sources]
        for source, future in zip(sources, futures):
            try:
                items = future.result()
                if not items:
                    raise ValueError("no usable public feed entries")
            except Exception as exc:
                print(f"{source['name']}: {exc}")
                failures.append(source["id"])
                continue
            successes += 1
            print(f"{source['name']}: {len(items)} entries; latest {max(item['date'] for item in items)[:10]}")
            for item in items:
                key = item["id"]
                if key in seen:
                    continue
                seen.add(key)
                if key in records:
                    item["discovered"] = records[key]["discovered"]
                records[key] = item
    if not successes:
        raise SystemExit("No feeds returned usable entries; leaving the previous snapshot intact.")
    ordered = sorted(records.values(), key=lambda item: item["date"], reverse=True)
    unique = {}
    for item in ordered:
        key = re.sub(r"[^\w]+", " ", item["title"].casefold()).strip()
        # Short recurring headings may be unrelated posts.
        if item["title"].startswith("Nugget ") and re.fullmatch(r"Nugget \d+", item["title"]):
            key = ("newsletter", item["source"], key)
        else:
            key = ("title", key, item["date"][:10]) if len(key) >= 25 else ("url", item["id"])
        unique.setdefault(key, item)
    public = [{k: s[k] for k in ("id", "name", "site", "description", "kind")} for s in sources]
    result = dict(updated=stamp.isoformat(), sources=public, failures=failures, items=list(unique.values())[:750])
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


if __name__ == "__main__":
    main()
