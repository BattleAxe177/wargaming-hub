# Wargaming Hub source-directory beta review

This branch **proposes** replacing the nine prototype sources with 21 independently selected historical hobby blogs. It is **not approved for merging yet**.

## Verification status
- The old sources are not grandfathered in. Some reappear because they fit the new editorial standard.
- Blogspot URLs use its conventional Atom endpoint, but live HTTP/Atom parsing for every feed has **not** been completed. Do not merge until a dry-run of `scripts/refresh.py` against this branch confirms source success/failure, recent publication dates, and appropriate article quality.
- The `sources.json` schema and existing refresh script are unchanged.
- Categories and source membership are **not** user favorites. The user's followed-source list remains empty unless explicitly set.
- Article-selection concern: `scripts/refresh.py` currently includes most usable posts. Wargame News and Terrain can dominate with promotional and nonhistorical material. Review exclusion or per-source caps before final activation.
- Several older blogs are included as high-quality archive candidates despite limited recent posting; identify stale ones during validation.

## Further candidates awaiting verified feed support
User-provided: Little Wars TV website, Little Wars TV YouTube, Sonic Sledgehammer Studio YouTube, Mark's Game Room YouTube, Wargames Soldiers & Strategy / Karwansaray.
Additional: Vis Lardica, Maidstone Wargames Society, Wyre Forest Gamers, Jemima Fawr, BoneSpoon Miniatures, Tales from a Wargame Shed, Battlegames.
Rules publishers and manufacturers: Too Fat Lardies, Baccus 6mm, Pendraken Miniatures, North Star Military Figures, Perry Miniatures, Gripping Beast, Wargames Foundry.
2D6 Wargaming is explicitly excluded pending evidence of renewed activity.

## Before merging
1. Test source feed retrieval and XML parsing for all 21 candidates in a network-enabled checkout; record passes and failures.
2. Confirm which inactive sources are worth retaining. Remove ones that do not return usable entries.
3. Resolve YouTube channel IDs and check current collector's XML behavior before adding feeds.
4. Find reliable RSS/Atom/API sources for manufacturers and news sites; don't invent endpoints.
5. Review content relevance and noise limits, especially Wargame News and Terrain.
6. Obtain user approval of the final directory, then merge the PR and manually run the existing Pages refresh.
