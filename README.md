# Wargaming Hub

A separate, static reader for historical miniature wargaming. Wargaming HQ informed the initial topic preferences, including compact tables, fast play, small scales, scenario design, Italian Wars, the Seven Days and Normandy. The site does not connect to HQ or require accounts. Saves, follows and the “seen” cutoff are stored in the current browser.

## Preview

Run `python -m http.server 8000 --directory docs` and open http://localhost:8000/. The checked-in feed snapshot works without a refresh. The standalone HTML distributed with the prototype contains that same snapshot and can also be opened directly in a browser.

## Refresh

Run `python scripts/refresh.py` with Python 3.10 or newer. Only public RSS and Atom endpoints in `sources.json` are fetched. The script keeps the last successful entries during partial outage, reports failures, and leaves the snapshot untouched if every source fails. A bounded archive preserves up to 750 entries. Canonical URLs strip tracking parameters, forum replies merge into a stable thread, and matching long titles on the same publication day are consolidated. Distinct reports of the same game from different authors are retained.

Editorial summaries and classification overrides for selected stories are in the source registry. Other entries get automatic descriptions from their type, period and available feed labels. Automatic categories can be imperfect. Article cards display a linked source-hosted photo when the blog feed supplies one over HTTPS. Forum threads and posts without an available image use text-only cards. “New” first highlights posts from the prior seven days. After marking new items as seen, it uses first discovery timestamps, so a newly indexed older post can still be new to the Hub.

## Source evaluation

The prototype tested the feeds directly. Eight independent blogs and the Pendraken Forum supplied recent entries. The active list includes Palouse Wargaming Journal, Grid Based Wargaming, Wargaming Miscellany, Battlefields & Warriors, Wargaming for Grown Ups, Der Alte Fritz Journal, Flintlock & Tomahawk and AJ’s Wargaming Table. Pendraken serves a public forum RSS stream. Off-topic threads and repeated replies would dominate this stream if ingested as individual articles.

Lead Adventure Forum, The Wargames Website, Wargames Illustrated and TooFatLardies returned HTTP 403 in this environment and were left out. The Dog’s Brush returned valid Atom but the latest entry was from 2017. The source registry lists the verified active inputs. Period filters span Ancients to Modern, though coverage depends on what the sources have published.

Private Facebook groups are outside this ingestion path. The Facebook Groups API was retired in April 2024. Meta’s Content Library API covers qualifying public material and Meta requires permission for automated collection. An authorized member can read or bookmark posts within Facebook, and group admins or authors can explicitly provide public links or opt-in material. There is no verified general-purpose private group feed for this prototype. Keep group-only posts and links out of the public repository and site.

- [Meta Content Library API scope](https://developers.facebook.com/docs/content-library-and-api/content-library-api/overview)
- [Meta’s automated collection policy explanation](https://about.fb.com/news/2021/04/how-we-combat-scraping/)
- [Groups API retirement details](https://www.sprinklr.com/help/articles/getting-started-facebook/meta-deprecates-facebook-groups-api/66229eb25f9dd9599d632712)

## Deploy after approval

Push the source to its own GitHub repository on `main`, configure Pages to use GitHub Actions, then set the repository Actions variable `HUB_PUBLISH_ENABLED` to `true`. Run the workflow manually once to verify the first deployment. The cron runs at 11:23 and 23:23 UTC, roughly morning and evening US Eastern. The workflow needs permission to write the feed snapshot back to `main`. If repository rules restrict writes, configure an authorized exception or update the persistence strategy before enabling the workflow. GitHub schedules can be delayed and public-repository schedules can be disabled after 60 days of inactivity.

- [Configure GitHub Pages](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)
- [GitHub Actions schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule)
