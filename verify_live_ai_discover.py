import json
import re
from pathlib import Path
from playwright.sync_api import expect, sync_playwright

edition = json.loads(Path("docs/assets/ai-discover.json").read_text())
site = "https://battleaxe177.github.io/wargaming-hub/?verify=3d48df76bc01e6a068d87c2cdc5acb73bb7152f6"
def start(context):
    page = context.new_page()
    page.goto(site + "#ai-discover")
    expect(page.locator(".card").first.get_by_role("heading")).to_have_text("Ticinus River 218 BC - Command and Colors Ancients Game", timeout=20000)
    return page

with sync_playwright() as p:
    browser = p.chromium.launch()
    first = start(browser.new_context())
    expect(first.locator(".tag.new")).to_have_count(0)
    context = browser.new_context(viewport={"width": 390, "height": 844})
    context.add_init_script("""if (!localStorage.getItem('wargaming-hub:v1')) {
      localStorage.setItem('wargaming-hub:v1', JSON.stringify({aiSeenThrough:'2026-11-21T13:30:10Z'}));
    }""")
    page = start(context)
    expect(page.locator(".tag.new")).to_have_count(8)
    top = page.locator(".card h3 a").all_text_contents()
    assert set(top[:8]) == {entry["title"] for entry in edition["items"] if entry["discoveredAt"].startswith("2026-11-22")}
    assert set(top[8:14]) == {entry["title"] for entry in edition["items"] if entry["discoveredAt"].startswith("2026-11-21")}
    assert "Year of the Four Emperors" in top[7]
    page.reload()
    expect(page.locator(".tag.new")).to_have_count(8)
    assert page.locator(".card h3 a").all_text_contents() == top
    page.get_by_role("combobox",name="Historical period").select_option("Ancients")
    expected = [title for title in top if any(e["title"]==title and "Ancients" in e["periods"] for e in edition["items"])]
    assert page.locator(".card h3 a").all_text_contents() == expected
    page.get_by_role("combobox",name="Content type").select_option("Battle report")
    expected = [title for title in expected if any(e["title"]==title and e["type"]=="Battle report" for e in edition["items"])]
    assert page.locator(".card h3 a").all_text_contents() == expected
    card = page.locator(".card").first
    for label in ("Like:", "Dislike:", "Save:"):
        button = card.get_by_role("button",name=re.compile("^"+label))
        button.click()
        expect(card.locator('button[aria-pressed="true"]').first).to_be_visible()
    follow = card.locator(".follow-source")
    follow.click()
    expect(follow).to_have_attribute("aria-pressed","true")
    with page.expect_download() as event:
        page.get_by_role("button",name="Export preferences").click()
    exported = json.loads(event.value.path().read_text())
    assert exported["savedArticles"] and exported["articleRatings"][0]["rating"] == "dislike"
    assert exported["discoveredSources"] or exported["followedSources"]
    page.get_by_role("button",name="Mark discoveries as seen").click()
    expect(page.locator(".tag.new")).to_have_count(0)
    page.reload()
    expect(page.locator(".card").first).to_be_visible()
    expect(page.locator(".tag.new")).to_have_count(0)
    page.get_by_role("link",name="Feed",exact=True).click()
    expect(page.locator(".card").first).to_be_visible()
    expect(page.get_by_role("checkbox",name="New only")).to_be_visible()
    expect(page.get_by_role("button",name="Mark discoveries as seen")).to_be_hidden()
    print("Live desktop and mobile: discovery order, historical dates, filtering, persistent badges, feedback, source following, and export passed.")
