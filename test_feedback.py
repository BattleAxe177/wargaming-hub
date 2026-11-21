import json
import os
import re
from pathlib import Path
from subprocess import Popen
from playwright.sync_api import sync_playwright, expect

os.chdir(Path(__file__).resolve().parent)
server = Popen(["python", "-m", "http.server", "8765", "--bind", "127.0.0.1", "--directory", "docs"])
url = "http://127.0.0.1:8765/"
try:
    with sync_playwright() as p:
        browser = p.chromium.launch( args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.goto(url)
        card = page.locator(".card").first
        like = card.get_by_role("button", name=re.compile(r"^Like:"))
        dislike = card.get_by_role("button", name=re.compile(r"^Dislike:"))
        like.focus()
        like.press("Enter")
        expect(like).to_have_attribute("aria-pressed", "true")
        url_key = page.evaluate("articleKey(document.querySelector('.card h3 a').href)")
        dislike.click()
        expect(like).to_have_attribute("aria-pressed", "false")
        expect(dislike).to_have_attribute("aria-pressed", "true")
        page.reload()
        expect(dislike).to_have_attribute("aria-pressed", "true")
        dislike.click()
        expect(dislike).to_have_attribute("aria-pressed", "false")
        card.get_by_role("button",name="Save:",exact=False).click()
        expect(card.get_by_role("button",name="Remove from saved:",exact=False)).to_have_attribute("aria-pressed","true")

        def export_prefs():
            with page.expect_download() as event:
                page.locator("#export-preferences").click()
            return json.loads(event.value.path().read_text())

        def import_prefs(data):
            page.locator("#preferences-file").set_input_files({
                "name":"preferences.json","mimeType":"application/json","buffer":json.dumps(data).encode()
            })
            expect(page.locator("#preferences-status")).to_have_text("Preferences imported and merged.")

        exported = export_prefs()
        clear = next(x for x in exported["articleRatings"] if x["url"] == url_key)
        assert clear["rating"] is None and exported["savedArticles"]
        other = {"url":"https://example.org/discontinued","rating":"like","updatedAt":"2026-07-01T00:00:00Z"}
        old = {**clear, "rating":"like", "updatedAt":"2023-01-01T00:00:00Z"}
        new = {**clear, "url":url_key + ("&" if "?" in url_key else "?") + "utm_source=test#section",
               "rating":"dislike","updatedAt":"2040-01-01T00:00:00Z"}
        base = {"format":exported["format"],"version":1,"followedSources":[],"savedArticles":[]}
        import_prefs({**base,"articleRatings":[old,other]})
        assert next(x for x in export_prefs()["articleRatings"] if x["url"] == url_key)["rating"] is None
        import_prefs({**base,"articleRatings":[new]})
        import_prefs(base)
        after = export_prefs()
        assert len(after["articleRatings"]) == 2 and after["savedArticles"]
        assert next(x for x in after["articleRatings"] if x["url"] == url_key)["rating"] == "dislike"

        ai = json.loads(Path("docs/assets/ai-discover.json").read_text())
        feed = json.loads(Path("docs/assets/feed.json").read_text())
        shared = next(x for x in feed["items"] if page.evaluate("(url) => articleKey(url)", x["url"]) == url_key)
        page.route("**/assets/ai-discover.json",lambda route: route.fulfill(json={**ai,"items":[{**shared,"url":new["url"]},*ai["items"]]}))
        page.reload()
        page.get_by_role("link",name="AI Discover",exact=True).click()
        expect(dislike).to_have_attribute("aria-pressed","true")
        like.click()
        expect(like).to_have_attribute("aria-pressed","true")
        expect(dislike).to_have_attribute("aria-pressed","false")
        follow = page.locator(".follow-source").first
        follow.click()
        expect(follow).to_have_attribute("aria-pressed","true")
        page.reload()
        expect(like).to_have_attribute("aria-pressed","true")
        expect(follow).to_have_attribute("aria-pressed","true")
        page.get_by_role("link",name="Sources",exact=True).click()
        expect(page.locator(".rating-controls")).to_have_count(0)
        page.locator("#results .save").first.click()

        def layout(view, width):
            page.set_viewport_size({"width":width,"height":900})
            page.get_by_role("link",name=view,exact=True).click()
            expect(page.locator(".rating-controls").first).to_be_visible()
            assert page.evaluate("""() => [...document.querySelectorAll('.rating-controls button')].every(button => {
              const rect = button.getBoundingClientRect(), parent = button.closest('.card').getBoundingClientRect();
              return rect.height >= 44 && rect.left >= parent.left && rect.right <= parent.right;
            })"""), (view, width)
        for width in (320, 390, 1440):
            for view in ("Feed","AI Discover"):
                layout(view,width)
        print("Passed desktop and mobile browser tests for both feeds, controls, persistence, preferences conflicts, Save, and Follow.")
finally:
    server.terminate()
    server.wait()
