# AI Discover editorial and source-discovery workflow

Use this guidance for future AI Discover research and updates in **BattleAxe177/wargaming-hub**. This does not trigger an unattended job on its own.

## Inputs
- The current `docs/assets/ai-discover.json`, `sources.json`, and existing published items to prevent duplicates.
- The user's most recent **manually uploaded** `wargaming-hub-preferences.json` (if supplied). Do not claim to have real-time access to in-browser preferences.
- Export format `wargaming-hub-preferences` version 1:
  - `savedArticles`: deliberately saved articles.
  - `followedSources`: currently approved sources explicitly followed.
  - `discoveredSources`: sources followed from AI Discover that are **candidate only**; fields include `site`, `name`, and `discoveredVia` (the article leading to the source). Older exports may omit this field.

## Editorial selection
- Use saved articles and followed sources as strong interest signals, but avoid turning the output into a narrow filter bubble.
- Aim for approximately 60% demonstrated interests, 25% related broadening topics, and 15% unexpected discoveries.
- Research interesting new content beyond the approved source directory; include different periods, scales, rules, terrain, scenarios, videos, and unusual good finds.
- Provide accurate source names, working original URLs, useful summaries and period/content labels. Include a canonical HTTPS `sourceUrl` (publisher/blog home or relevant channel page) for each new AI Discover article to improve Follow source accuracy; otherwise the site falls back to the article URL's origin.
- Do not assume all articles from followed sources are relevant; evaluate independently and avoid duplicates.
- Use original-source imagery only when embedding or reuse is permitted and attributable; leave cards text-only otherwise.

## Organic source discovery (each editorial refresh)
1. Read `discoveredSources` in the user-supplied export; treat these as **priority evaluation candidates**, not automatically approved feeds.
2. Also consider blogs, video channels, publishers, forums, and social accounts that yielded multiple worthwhile articles during the current research.
3. Compare against `sources.json` by canonical website/domain and known feed URL, including redirects and aliases.
4. Validate candidates: topical relevance, history of worthwhile posts, recent activity, usable public RSS/Atom/YouTube feed or legitimately available API, response and parsing success, appropriate metadata/image behavior, and expected content volume.
5. Flag irrelevant, inactive, unreliable, private, access-restricted, or feedless candidates rather than inventing feed endpoints or scraping private content.
6. Recommend promising candidates with evidence, feed URL, reasons to include, risks (e.g. too many promotional posts), and provenance (`user-follow` or `AI-discovered`).
7. **Create a SEPARATE pull request** proposing only validated changes to `sources.json` (and collector code only if explicitly authorized). Do not merge this PR automatically; human approval is required before any source enters the regular feed.
8. Create the separate AI Discover editorial PR, or update the edition as explicitly requested; do not silently merge/publish it.
9. Report counts for researched, verified, proposed, rejected/deferred candidate sources, including any permission or technical blockers.

## Local follow semantics
- The `Follow source` button on AI Discover is a preference signal, not approval for the regular feed.
- Candidate follows are kept locally and exported manually. Import between devices merges them.
- An existing approved source followed from AI Discover is placed in `followedSources`; an unfamiliar publisher is placed in `discoveredSources`.
- No browser analytics, remote automatic sync, or server-side behavioral collection is enabled.
