const assert = require("node:assert/strict");
const fs = require("node:fs");
const vm = require("node:vm");
const {test} = require("node:test");

const app = fs.readFileSync("docs/assets/app.js", "utf8").replace(/initialize\(\);\s*$/, "");
const old = "2026-11-21T08:00:00Z";
const fresh = "2026-11-22T08:00:00Z";

function load(previous = {}) {
  let saved = JSON.stringify(previous);
  const localStorage = {getItem: () => saved, setItem: (_, value) => { saved = value; }};
  const context = vm.createContext({URL, localStorage});
  vm.runInContext(app, context);
  return {
    run: source => vm.runInContext(source, context),
    get saved() { return JSON.parse(saved); }
  };
}

test("AI discoveries sort by discovery, then publication and canonical URL", () => {
  const app = load();
  const ordered = app.run(`[
    {url: "https://example.net/z", discoveredAt: "${old}", date: "2026-11-21"},
    {url: "https://example.net/c", discoveredAt: "${fresh}", date: "2020-01-01"},
    {url: "https://example.net/b?utm_source=test", discoveredAt: "${fresh}", date: "2020-01-01"},
    {url: "https://example.net/a", discoveredAt: "${fresh}", date: "2019-01-01"},
    {url: "https://example.net/legacy", date: "2026-11-22"}
  ].sort(compareDiscoveries).map(item => articleKey(item.url).split("/").at(-1)).join(",")`);
  assert.equal(ordered, "b,c,a,z,legacy");
});

test("legacy preferences, first-visit baseline, persistent badges and acknowledgement", () => {
  const legacy = load({seenThrough: "regular-feed-cutoff", followed: ["publisher"]});
  assert.equal(legacy.run("state.aiSeenThrough"), null);
  assert.equal(legacy.run(`isNewDiscovery({discoveredAt: "${old}"})`), false);
  legacy.run(`aiEdition = {items: [{discoveredAt: "${old}"}]}; acknowledgeDiscoveries();`);
  assert.equal(legacy.saved.aiSeenThrough, old);
  assert.equal(legacy.saved.seenThrough, "regular-feed-cutoff");
  assert.deepEqual(legacy.saved.followed, ["publisher"]);
  const returning = load(legacy.saved);
  returning.run(`aiEdition = {items: [{discoveredAt: "${fresh}"}, {discoveredAt: "${old}"}]};`);
  assert.equal(returning.run("isNewDiscovery(aiEdition.items[0])"), true);
  assert.equal(returning.run("isNewDiscovery(aiEdition.items[0])"), true);
  assert.equal(returning.run("isNewDiscovery(aiEdition.items[1])"), false);
  assert.equal(returning.run("isNewDiscovery({date: '2026-11-22'})"), false);
  returning.run("acknowledgeDiscoveries()");
  assert.equal(returning.run("isNewDiscovery(aiEdition.items[0])"), false);
  assert.equal(returning.saved.aiSeenThrough, fresh);
});

test("AI Discover hides regular-feed duplicates and keeps other posts from the source", () => {
  const app = load();
  const titles = app.run(`uniqueAiDiscoveries([
    {url: "https://example.net/post?utm_source=editorial", title: "Duplicate"},
    {url: "https://example.net/other-post", title: "Different article"},
    {url: "https://elsewhere.net/post", title: "Other source"}
  ], [{url: "http://example.net/post/?m=1#comments"}]).map(item => item.title).join(",")`);
  assert.equal(titles, "Different article,Other source");
});
