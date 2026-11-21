"use strict";

const $ = (id) => document.getElementById(id);
const periods = ["Ancients", "Medieval", "Renaissance", "18th Century", "Napoleonic", "American Civil War",
  "19th Century", "World War I", "Interwar", "World War II", "Modern", "Mixed & general"];
const kinds = ["Battle report", "Painting & modeling", "Scenario & rules", "Forum discussion", "Hobby news", "Hobby journal"];
const familiar = new Set(["Ancients", "Medieval", "Renaissance", "Napoleonic", "American Civil War", "World War II"]);
const views = {
  feed: ["The latest dispatches", "Historical wargaming from across the web."],
  discover: ["Discover", "Start with a period beyond your usual projects, or try a recommendation inspired by them."],
  "ai-discover": ["AI Discover", "An experimental edition curated by ChatGPT Work."],
  saved: ["Saved articles", "Your reading list on this device."],
  sources: ["Source directory", "Follow an independent blog or community to find its posts quickly."]
};
const dateLabel = new Intl.DateTimeFormat(undefined, {dateStyle: "medium"});
const calendarDateLabel = new Intl.DateTimeFormat(undefined, {dateStyle: "medium", timeZone: "UTC"});
const formatDate = (date) => (date.length === 10 ? calendarDateLabel : dateLabel).format(new Date(date));
const STORAGE = "wargaming-hub:v1";

function loadState() {
  try {
    const state = JSON.parse(localStorage.getItem(STORAGE)) || {};
    return {
      saved: new Map(Object.entries(state.saved || {})),
      followed: new Set(state.followed || []),
      discoveredSources: new Map(Object.entries(state.discoveredSources || {})),
      seenThrough: typeof state.seenThrough === "string" ? state.seenThrough : ""
    };
  } catch {
    return {saved: new Map(), followed: new Set(), discoveredSources: new Map(), seenThrough: ""};
  }
}

const state = loadState();
let snapshot;
let sources;
let aiEdition;
let aiUnavailable = false;
const FEED_PAGE_SIZE = 18;
let limit = FEED_PAGE_SIZE;

function persist() {
  try {
    localStorage.setItem(STORAGE, JSON.stringify({
      saved: Object.fromEntries(state.saved), followed: [...state.followed],
      discoveredSources: Object.fromEntries(state.discoveredSources), seenThrough: state.seenThrough
    }));
  } catch {
    $("storage-note").hidden = false;
  }
}

function buttonState(button, active, label, activeLabel) {
  button.setAttribute("aria-pressed", String(active));
  button.querySelector(".save-label").textContent = active ? activeLabel : label;
}

function fillSelect(select, defaultLabel, options) {
  select.replaceChildren(...["", ...options].map((option) => new Option(option || defaultLabel, option)));
}

function tag(container, label, extra = "") {
  const element = document.createElement("span");
  element.className = extra ? "tag " + extra : "tag";
  element.textContent = label;
  container.append(element);
}

function isNew(item) {
  return item.discovered > state.seenThrough &&
    (state.seenThrough || Date.parse(item.date) >= Date.parse(snapshot.updated) - 7 * 86400000);
}


function sourceWebsite(item) {
  try {
    const address = new URL(item.sourceUrl || item.url);
    if (address.protocol !== "https:" && address.protocol !== "http:") return "";
    return address.origin + "/";
  } catch {
    return "";
  }
}

function discoverSource(item) {
  const site = sourceWebsite(item);
  if (!site) return null;
  const host = new URL(site).hostname.replace(/^www\./, "").toLowerCase();
  const approved = [...sources.values()].find(source => {
    try { return new URL(source.site).hostname.replace(/^www\./, "").toLowerCase() === host; }
    catch { return false; }
  });
  if (approved) return {id: approved.id, name: approved.name, site: approved.site, approved: true};
  return {id: site, name: item.sourceName || item.source || host, site, approved: false};
}

function followSourceButton(item) {
  const source = discoverSource(item);
  if (!source) return null;
  const button = document.createElement("button");
  button.type = "button";
  button.className = "follow-source";
  const update = () => {
    const following = source.approved ? state.followed.has(source.id) : state.discoveredSources.has(source.id);
    button.textContent = following ? "✓ Following source" : "+ Follow source";
    button.setAttribute("aria-pressed", String(following));
    button.setAttribute("aria-label", (following ? "Unfollow " : "Follow ") + source.name);
    button.title = source.approved ? "Approved regular-feed source" : "Candidate source for review; not yet in the regular feed";
  };
  button.addEventListener("click", () => {
    if (source.approved) {
      if (state.followed.has(source.id)) state.followed.delete(source.id);
      else state.followed.add(source.id);
    } else if (state.discoveredSources.has(source.id)) {
      state.discoveredSources.delete(source.id);
    } else {
      state.discoveredSources.set(source.id, {
        name: source.name, site: source.site, discoveredVia: item.url,
        status: "candidate"
      });
    }
    persist();
    update();
  });
  update();
  return button;
}

function articleCard(item, discover, featured) {
  const node = $("article-template").content.cloneNode(true);
  const tags = node.querySelector(".tags");
  if (featured) {
    node.querySelector(".card").classList.add("featured");
    tag(tags, "Editor’s pick", "editor-pick");
  }
  for (const period of item.periods) tag(tags, period);
  tag(tags, item.type);
  if (isNew(item)) tag(tags, "New", "new");
  const sourceName = sources.get(item.source)?.name || item.sourceName || item.source;
  node.querySelector(".byline").textContent = item.date ? sourceName + " · " + formatDate(item.date) : sourceName;
  const title = node.querySelector("h3 a");
  title.textContent = item.title;
  for (const link of [title, node.querySelector(".outbound")]) {
    link.href = item.url;
    link.target = "_blank";
    link.rel = "noopener noreferrer";
  }
  node.querySelector(".summary").textContent = item.summary;
  if (item.image && /^https:\/\//i.test(item.image)) {
    const image = document.createElement("img");
    image.className = "article-photo";
    image.alt = item.imageRights?.alt || "";
    image.loading = "lazy";
    image.decoding = "async";
    image.referrerPolicy = "no-referrer";
    const card = node.querySelector(".card");
    card.prepend(image);
    const rights = item.imageRights;
    let credit;
    if (rights?.credit && rights.license && /^https:\/\//i.test(rights.licenseUrl)) {
      credit = document.createElement("p");
      credit.className = "image-credit";
      for (const [label, href] of [[rights.credit, item.url], [rights.license, rights.licenseUrl]]) {
        const link = document.createElement("a");
        link.textContent = label;
        link.href = href;
        link.target = "_blank";
        link.rel = "noopener noreferrer";
        if (credit.hasChildNodes()) credit.append(" · ");
        credit.append(link);
      }
      image.after(credit);
      if (rights.preserveFrame) image.classList.add("full-frame");
    }
    image.addEventListener("error", () => {
      image.remove();
      credit?.remove();
    }, {once: true});
    image.src = item.image;
  }
  const outside = item.periods.some((period) => period !== "Mixed & general" && !familiar.has(period));
  node.querySelector(".context").textContent = discover && outside ? "Outside your usual periods" : item.interests.slice(0, 2).join(" · ");
  const save = node.querySelector(".save");
  const updateButton = () => {
    const saved = state.saved.has(item.id);
    buttonState(save, saved, "Save", "Saved");
    save.setAttribute("aria-label", (saved ? "Remove from saved: " : "Save: ") + item.title);
  };
  save.onclick = () => {
    if (state.saved.has(item.id)) state.saved.delete(item.id);
    else state.saved.set(item.id, {...item, sourceName});
    persist();
    if (activeView() === "saved") {
      render();
      ($("results").querySelector(".save") || $("view-title")).focus();
    } else updateButton();
  };
  updateButton();
  if (activeView() === "ai-discover") {
    const follow = followSourceButton(item);
    if (follow) node.querySelector(".card-top").append(follow);
  }
  return node;
}

function sourceCard(source) {
  const node = $("article-template").content.cloneNode(true);
  tag(node.querySelector(".tags"), source.kind);
  node.querySelector(".byline").remove();
  const title = node.querySelector("h3 a");
  title.textContent = source.name;
  title.href = source.site;
  node.querySelector(".summary").textContent = source.description;
  const outbound = node.querySelector(".outbound");
  outbound.textContent = "Visit source";
  outbound.href = source.site;
  const save = node.querySelector(".save");
  const update = () => {
    const followed = state.followed.has(source.id);
    buttonState(save, followed, "Follow", "Following");
    save.setAttribute("aria-label", (followed ? "Unfollow " : "Follow ") + source.name);
  };
  save.onclick = () => {
    if (state.followed.has(source.id)) state.followed.delete(source.id);
    else state.followed.add(source.id);
    persist();
    update();
  };
  update();
  return node;
}

function activeView() {
  const view = location.hash.slice(1);
  return Object.hasOwn(views, view) ? view : "feed";
}

function discovery(items) {
  const outside = (item) => item.periods.find((p) => p !== "Mixed & general" && !familiar.has(p));
  const candidates = [];
  const remaining = [];
  const used = new Set();
  for (const item of items) {
    const period = outside(item);
    if (period && !used.has(period)) {
      candidates.push(item);
      used.add(period);
    } else remaining.push(item);
  }
  const relevant = (item) => item.interests.length || item.periods.some((period) => familiar.has(period));
  const recommendations = remaining.filter((item) => !outside(item) && relevant(item));
  const exploration = remaining.filter((item) => outside(item));
  return [
    ...candidates.slice(0, 3),
    ...recommendations.slice(0, 3),
    ...candidates.slice(3),
    ...exploration,
    ...recommendations.slice(3)
  ];
}

async function loadAiEdition() {
  try {
    const response = await fetch("./assets/ai-discover.json");
    if (!response.ok) throw new Error("AI edition unavailable");
    const edition = await response.json();
    const seen = new Set();
    const items = [];
    for (const item of edition.items) {
      if (typeof item.url !== "string" || !/^https:\/\//i.test(item.url) || seen.has(item.url)) continue;
      seen.add(item.url);
      items.push({
        ...item, id: item.url,
        date: typeof item.date === "string" && Number.isFinite(Date.parse(item.date)) ? item.date : null,
        image: (typeof item.image === "string" && /^https:\/\//i.test(item.image)) ? item.image : undefined
      });
    }
    aiEdition = {...edition, items};
  } catch {
    aiUnavailable = true;
  }
  if (activeView() === "ai-discover") render();
}

function rankFeed(records) {
  const savedTopics = new Set(
    [...state.saved.values()].flatMap(item => item.interests || [])
  );
  const hour = 60 * 60 * 1000;
  return records.map(item => {
    const topics = new Set(item.interests.filter(topic => savedTopics.has(topic)));
    const topicBoost = Math.min(topics.size, 2) * 12;
    const followBoost = state.followed.has(item.source) ? 6 : 0;
    const forumDelay = sources.get(item.source)?.kind === "Forum" ? 12 : 0;
    return {item, priority: Date.parse(item.date) + (topicBoost + followBoost - forumDelay) * hour};
  }).sort((a, b) => b.priority - a.priority).map(({item}) => item);
}

function balanceFirstPage(records) {
  const selected = [];
  const deferred = [];
  const counts = new Map();
  const candidates = records.slice(0, FEED_PAGE_SIZE * 2);
  for (const item of candidates) {
    const count = counts.get(item.source) || 0;
    if (count >= 3 || selected.length >= FEED_PAGE_SIZE) {
      deferred.push(item);
      continue;
    }
    selected.push(item);
    counts.set(item.source, count + 1);
  }
  return [...selected, ...deferred, ...records.slice(candidates.length)];
}


function exportPreferences() {
  const savedArticles = [...state.saved.values()].map(item => ({
    url: item.url, title: item.title, source: item.source || "",
    sourceName: item.sourceName || "", periods: item.periods || [],
    type: item.type || "", interests: item.interests || []
  }));
  const preferences = {
    format: "wargaming-hub-preferences", version: 1,
    exportedAt: new Date().toISOString(),
    note: "Saves and follows are explicit interests. This export contains no click history.",
    followedSources: [...state.followed].map(id => ({id, name: sources?.get(id)?.name || id})),
    savedArticles,
    discoveredSources: [...state.discoveredSources.entries()].map(([site, info]) => ({
      site, name: info.name, discoveredVia: info.discoveredVia, status: "candidate"
    }))
  };
  const blob = new Blob([JSON.stringify(preferences, null, 2)], {type: "application/json"});
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "wargaming-hub-preferences.json";
  document.body.append(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
  $("preferences-status").textContent = "Preferences exported. Share the JSON file with ChatGPT Work.";
}

async function importPreferences(file) {
  if (!file) return;
  if (file.size > 2000000) throw new Error("File is too large.");
  const preferences = JSON.parse(await file.text());
  if (preferences.format !== "wargaming-hub-preferences" ||
      preferences.version !== 1 ||
      !Array.isArray(preferences.followedSources) ||
      !Array.isArray(preferences.savedArticles)) {
    throw new Error("Not a valid Wargaming Hub preferences file.");
  }
  for (const entry of preferences.followedSources.slice(0,1000)) {
    if (typeof entry?.id === "string" && entry.id.length < 200)
      state.followed.add(entry.id);
  }
  for (const source of (Array.isArray(preferences.discoveredSources) ? preferences.discoveredSources : []).slice(0,1000)) {
    if (typeof source?.site !== "string" || !source.site.startsWith("https://") ||
        typeof source.name !== "string" || source.name.length > 250) continue;
    const website = sourceWebsite({url: source.site});
    if (website) state.discoveredSources.set(website, {
      name: source.name, site: website,
      discoveredVia: typeof source.discoveredVia === "string" ? source.discoveredVia : "",
      status: "candidate"
    });
  }
  for (const article of preferences.savedArticles.slice(0,1000)) {
    if (typeof article?.url === "string" && article.url.startsWith("https://") &&
        typeof article.title === "string" && article.title.length < 500)
      state.saved.set(article.url, {...article, id: article.url});
  }
  persist();
  render();
}

function render() {
  if (!snapshot) return;
  const view = activeView();
  const aiView = view === "ai-discover";
  for (const link of $("navigation").querySelectorAll("a")) {
    if (link.hash === "#" + view) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  }
  $("hero").hidden = view !== "feed";
  [$("view-title").textContent, $("view-description").textContent] = views[view];
  $("filters").hidden = view === "sources";
  $("feed-toggles").hidden = aiView;
  $("mark-read").hidden = view !== "feed" || !snapshot.items.some(isNew);
  const failed = snapshot.failures.length;
  $("updated").textContent = aiView
    ? (aiEdition?.updated ? "Edition " + formatDate(aiEdition.updated) : "")
    : "Feed checked " + formatDate(snapshot.updated) + (failed ? " · " + failed + " unavailable" : "");
  if (aiView && !aiEdition) {
    $("count").textContent = "";
    $("more").hidden = true;
    $("results").textContent = aiUnavailable ? "AI Discover couldn’t be loaded. Reload the page to try again." : "Loading AI Discover…";
    return;
  }
  const items = aiView ? aiEdition.items : view === "saved" ? [...state.saved.values()].reverse() : snapshot.items;
  const filtered = items.filter((item) =>
    (!$("period").value || item.periods.includes($("period").value)) &&
    (!$("kind").value || item.type === $("kind").value) &&
    (aiView || !$("following").checked || state.followed.has(item.source)) &&
    (aiView || !$("fresh").checked || isNew(item))
  );
  let records = view === "sources" ? snapshot.sources : view === "discover" ? discovery(filtered) : filtered;
  if (view === "feed" && !$("kind").value && !$("following").checked) {
    records = rankFeed(records);
  }
  const filterActive = $("period").value || $("kind").value || $("following").checked || $("fresh").checked;
  const featured = view === "feed" && !filterActive && records.find((item) =>
    item.featured && item.image && Date.parse(item.date) >= Date.parse(snapshot.updated) - 14 * 86400000
  );
  if (featured) records = [featured, ...records.filter((item) => item !== featured)];
  if (view === "feed" && !filterActive) records = balanceFirstPage(records);
  const label = view === "sources" ? "source" : "article";
  $("count").textContent = records.length + " " + label + (records.length === 1 ? "" : "s");
  $("more").hidden = records.length <= limit;
  const results = $("results");
  results.replaceChildren(...records.slice(0, limit).map((item) =>
    view === "sources" ? sourceCard(item) : articleCard(item, view === "discover", item === featured)));
  if (!records.length) {
    const empty = document.createElement("p");
    empty.className = "empty";
    empty.textContent = view === "saved" && !state.saved.size
      ? "Save an article from the feed to start your reading list."
      : "No articles match. Try changing the filters.";
    results.append(empty);
  }
}

async function initialize() {
  try {
    snapshot = window.WARGAMING_SNAPSHOT || await fetch("./assets/feed.json").then((response) => {
      if (!response.ok) throw new Error("Feed unavailable");
      return response.json();
    });
    sources = new Map(snapshot.sources.map((source) => [source.id, source]));
    fillSelect($("period"), "All periods", periods);
    fillSelect($("kind"), "All types", kinds);
    const initialLimit = () => activeView() === "ai-discover" ? 25 : FEED_PAGE_SIZE;
    limit = initialLimit();
    for (const input of $("filters").querySelectorAll("input,select")) input.onchange = () => { limit = initialLimit(); render(); };
    $("more").onclick = () => {
      const next = limit;
      limit += FEED_PAGE_SIZE;
      render();
      $("results").children[next]?.querySelector("h3 a")?.focus();
    };
    $("mark-read").onclick = () => { state.seenThrough = snapshot.updated; persist(); render(); $("view-title").focus(); };
    window.addEventListener("hashchange", () => {
      limit = initialLimit();
      for (const field of $("filters").querySelectorAll("select")) field.value = "";
      for (const field of $("filters").querySelectorAll("input")) field.checked = false;
      render();
      $("view-title").focus();
    });
    $("export-preferences").onclick = exportPreferences;
    $("import-preferences").onclick = () => $("preferences-file").click();
    $("preferences-file").onchange = async event => {
      try {
        await importPreferences(event.target.files?.[0]);
        $("preferences-status").textContent = "Preferences imported and merged.";
      } catch (error) {
        $("preferences-status").textContent = "Import failed: " + error.message;
      }
      event.target.value = "";
    };
    render();
    loadAiEdition();
  } catch {
    $("results").textContent = "The feed couldn’t be loaded. Reload the page to try again.";
  }
}

initialize();
