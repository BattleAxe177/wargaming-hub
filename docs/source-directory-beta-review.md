# Wargaming Hub source-directory beta review

PR #4 proposes replacing the nine prototype inputs with 28 validated sources. The branch is ready for review. The live directory changes after a separately approved merge and a successful Pages refresh.

## Validation on November 20, 2026

The production collector fetched the source URLs, parsed RSS or Atom, and checked usable dates and original links. Two full network-enabled runs from the same committed snapshot passed for all 28 sources, with 555 unique articles after history retention and deduplication. The eligible counts below are the second run's usable entries per feed before cross-feed deduplication. No live GitHub Actions runner was used for these validation runs.

| Source | Type | Eligible entries | Latest eligible date (UTC) |
| --- | --- | ---: | --- |
| [Yarkshire Gamer](https://yarkshiregamer.blogspot.com/) | Independent blog | 25 | 2026-11-15 |
| [Sgt Steiner's Wargaming Blog](https://sgtsteiner.blogspot.com/) | Independent blog | 25 | 2026-11-19 |
| [Wargame News and Terrain](https://wargameterrain.blogspot.com/) | Independent blog | 6 | 2026-11-18 |
| [Der Alte Fritz Journal](https://altefritz.blogspot.com/) | Independent blog | 24 | 2026-10-22 |
| [Shaun's Wargaming with Miniatures](https://shaun-wargaming-minis.blogspot.com/) | Independent blog | 25 | 2026-10-26 |
| [Grid Based Wargaming](https://gridbasedwargaming.blogspot.com/) | Independent blog | 25 | 2026-11-18 |
| [Palouse Wargaming Journal](https://palousewargamingjournal.blogspot.com/) | Independent blog | 25 | 2026-11-17 |
| [Wargaming Miscellany](https://wargamingmiscellany.blogspot.com/) | Independent blog | 25 | 2026-11-20 |
| [Battlefields & Warriors](https://battlefieldswarriors.blogspot.com/) | Independent blog | 25 | 2026-10-19 |
| [Wargaming for Grown Ups](https://wargaming4grownups.blogspot.com/) | Independent blog | 25 | 2026-11-06 |
| [Heretical Gaming](https://hereticalgaming.blogspot.com/) | Independent blog | 25 | 2026-08-04 |
| [Bloody Big BATTLES!](https://bloodybigbattles.blogspot.com/) | Independent blog | 25 | 2026-11-18 |
| [Grymauch's Solo Wargaming](https://grymauch.blogspot.com/) | Independent blog | 25 | 2026-11-18 |
| [Small but Perfectly Formed](https://elenderilsblog.blogspot.com/) | Independent blog | 25 | 2026-11-10 |
| [Independent Wargames Group](https://independentwargamesgroup.blogspot.com/) | Independent blog | 23 | 2026-09-20 |
| [AJ's Wargaming Table](https://ajstable.blogspot.com/) | Independent blog | 25 | 2026-11-08 |
| [Flintlock & Tomahawk](https://flintlockandtomahawk.blogspot.com/) | Independent blog | 25 | 2026-11-20 |
| [Little Wars TV](https://www.youtube.com/c/LittleWarsTV) | YouTube | 15 | 2026-11-17 |
| [Sonic Sledgehammer Studio](https://www.youtube.com/@SonicSledgehammerStudio) | YouTube | 5 | 2026-11-10 |
| [Mark’s Game Room](https://www.youtube.com/@MarksGameRoom) | YouTube | 12 | 2026-11-13 |
| [Wargames, Soldiers & Strategy](https://www.karwansaraypublishers.com/blogs/wss-blog) | Publisher | 29 | 2026-11-18 |
| [Warlord Games Community](https://warlord-community.warlordgames.com/) | Manufacturer | 6 | 2026-11-18 |
| [Wargames Atlantic](https://wargamesatlantic.com/blogs/news) | Manufacturer | 5 | 2026-11-13 |
| [Pendraken Miniatures](https://www.pendraken.co.uk/) | Manufacturer | 12 | 2026-11-17 |
| [Battlegames](https://battlegames.co.uk/) | Publisher | 10 | 2026-11-10 |
| [Wargames Illustrated](https://www.wargamesillustrated.net/) | Publisher | 7 | 2026-07-20 |
| [Dust, Tears & Dice](https://dusttears.blogspot.com/) | Independent blog | 25 | 2026-11-15 |
| [Le Coq Fou](https://lecoqfou.blogspot.com/) | Independent blog | 25 | 2026-11-15 |

## Editorial selection

- Wargame News and Terrain must tag entries historical. Mixed fantasy and science-fiction releases and selected generic promotions are screened out. Genuinely historical release news, rules and terrain still qualify.
- Sonic Sledgehammer Studio, Mark’s Game Room, Warlord Games Community, Wargames Atlantic, Pendraken Miniatures, and Wargames, Soldiers & Strategy have source-specific title and category rules. These aim to retain historical coverage and sidestep unrelated product lines, pure sales, or off-topic uploads on the broadest feeds. The rules are deliberately narrow for mixed catalogs and may miss articles with vague titles.
- The three YouTube channels use their official Atom endpoints. The collector uses media descriptions for classification when the entry lacks an article body and retains feed-provided thumbnails and watch links.
- Sources are collection inputs. Existing followed-source preferences and the separate AI Discover edition are unaffected.

## Sources held back

| Candidates | Result |
| --- | --- |
| Olicanalad’s Games, Roundwood’s World, Wargaming with Silver Whistle, Gaming with TooFatLardies | All parsed. Latest usable dates were December 2024, January 2025, February 2023, and December 2025, respectively. Held for archive discovery because they had no eligible item in the preceding six months. |
| Little Wars TV website, Baccus 6mm, Helion | No suitable feed verified on the reviewed pages. Little Wars TV is included through its YouTube feed. |
| Too Fat Lardies official site, Perry Miniatures, Footsore, legacy Warlord site, krigsspil.dk | Tested feeds parsed but were stale. The contemporary Warlord Community feed takes the Warlord slot. |
| North Star Military Figures | RSS worked, but the recent sample mostly concerned fantasy or mixed content, with little historical throughput. |
| Osprey, Victrix, GMDS | Tested URLs returned HTTP 500, 404 and 503, respectively. These results apply to the tested URLs. |
| Tabletop Gaming, The Wargames Website, Pendraken Forum | Accessible, but the reviewed samples leaned toward board-game news, mixed promotional releases or repeated forum replies. The official Pendraken manufacturer feed qualified after historical filtering. |
| 2D6 Wargaming | Excluded as discussed. |

## Feed variety

The original 21 candidates parsed, but Wargame News and Terrain occupied 7 of the first 18 articles and 13 of the first 30 before historical filtering. The final filtered directory already reduced its share to 2 of the first 18, with 12 sources represented and no source above 3 entries. Applied by itself to the original sample, the three-per-source preference reduced the busiest source from 7 to 4 after fallback. On the final filtered sample, a two-per-source preference added one more source but reached two days further back. A three-per-source preference left the opening 18 in date order in both final dry runs.

The PR keeps that preference as a guardrail for future bursts. In the unfiltered main feed, the first 18 cards can draw from the first 36 chronological candidates to favor up to three per source when there are enough alternatives. The same check with a simulated high-volume source moved extras below the opening page without deleting articles. The feed falls back to the deferred entries if the candidate window is too quiet. Explicit filters and saved articles retain their existing ordering behavior.

Review the directory before merging, then verify the first deployed refresh from the GitHub Actions runner. The branch contains no generated feed snapshot or workflow changes.
