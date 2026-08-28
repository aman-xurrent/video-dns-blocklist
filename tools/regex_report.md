# Blocklist regex compression report

**Inputs**

| File | Count | Role |
|---|---|---|
| `/tmp/rgx/must_cover_curated.txt` | 494 | hand-verified curated blocklist domains. Every one must end up blocked. |
| `/tmp/rgxverify/must_cover_subdomains.txt` | 2964 | the 494 expanded with `www.`, `m.`, `proxy.`, `cdn.`, `api.`. This is what the `\|\|domain^` literal rules actually covered. |
| `/tmp/rgx/guard3.txt` | 129 | must never be blocked. Zero effective hits required. |
| `/tmp/rgxverify/top20k.txt` | 20000 | Cisco Umbrella top domains, used as a collateral-damage sweep. |
| `/tmp/rgx/keep_literal.txt` | 260 | stays as literal rules, untouched by this work. |

The old 1148-domain extended section from The Block List Project is gone. It contained
`nasa.gov`, `worldwind.arc.nasa.gov`, `webcast.berkeley.edu`, `gutenberg.org` and `pbs.org`, all of
which once ran a BitTorrent tracker and none of which should be blocked. `must_cover.txt` is
obsolete.

---

## The thing that changed everything: regex rules do not match subdomains

An adblock literal rule `||1337x.to^` blocks `1337x.to`, `www.1337x.to` and `proxy.1337x.to`. A
regex rule does not do that. It is tested against the full hostname with no host-suffix logic, so
`/^1337x\./` only ever matches the apex and every subdomain leaks through.

That invalidated 23 of the 92 patterns in the previous run. Measured against the 2964 expanded
hostnames, the old set matched 1495 and missed 1469, roughly half the real coverage.

**The fix, applied throughout:** replace a hard `^` anchor with `(^|\.)`, which is the regex
equivalent of what `||domain^` does and is RE2 safe. Where the source data also has hyphen-joined
forms (`wide-youtube.l.google.com`, `hd-torrents.org`) the prefix is `(^|[.-])` instead.

Widening for subdomains and tightening for guards had to be done in the same pass, not one after
the other, because `(^|\.)` also widens what can match.

**Why this is equivalent to the literal it replaces, not just a fit to the five test prefixes.** The
verifier only tests `www.`, `m.`, `proxy.`, `cdn.` and `api.`, but `||domain^` covers subdomains of
any depth. The patterns match any depth too, structurally: any subdomain of `tracker.army` contains
`.tracker.`, any subdomain of `123movies.net` contains `.123movies`, any subdomain of `youtu.be`
ends in `.youtu.be`. So `dl.tracker.army` and `t.yts.am` are covered as well. The unanchored
substring patterns (`/eztv/`, `/rarbg/`, `/warez/`) were never affected by the subdomain problem at
all.

---

## Exception rules

Two `@@` rules ship at the bottom of `regexes.txt`. They are in the same file on purpose: if
someone loads `regexes.txt` without them, `music.youtube.com` gets blocked and the headline feature
breaks silently. Exception rules beat regex block rules in the AdGuard DNS engine, verified against
`github.com/AdguardTeam/urlfilter`.

| Rule | Why |
|---|---|
| `@@/(^\|\.)music\.youtube\.com$/` | The whole point of the list is that YouTube goes away and YouTube Music keeps working. `(^\|[.-])youtube\.` cannot tell `m.youtube.com` (block) from `music.youtube.com` (allow) by shape, and an allowlist of permitted subdomain labels would be far more brittle than one exception. |
| `@@/\.(internal\|local\|corp\|lan\|home\|intranet)$/` | Protects every private/internal namespace from every pattern, not just the tracker one. This is what lets `/(^\|\.)tracker[0-9]?\./` stay one short readable line instead of a 3000-character TLD alternation. |

Neither exception matches any of the 2964 target hostnames. The verifier asserts that directly.

---

## The four confirmed false positives, and what was done

### 1. `/ncore\./` matched `encore.scdn.co`

`scdn.co` is Spotify's CDN. Fixed by anchoring to a label boundary: **`/(^|\.)ncore\./`**. It now
needs `ncore.` to start the hostname or follow a dot. `encore.scdn.co` has an `e` in front, so it
cannot match. The same fix incidentally clears `screencore.io` and `cs.screencore.io`, which were
also being hit in the top 20k.

### 2. `/torrents/` matched `academictorrents.com` and `legittorrents.info`

Both are legal distribution services. Academic Torrents distributes research datasets.

`/torrents/` was **deleted outright**. Its sole-coverage count was zero, meaning every host it
matched was already matched by another pattern, so it bought nothing and cost two false positives.

That left `academictorrents.com` still matched by `/[a-su-z0-9-]torrent/` on the `c` in
`academi**c**torrents`. The character class was narrowed to **`/[a-bd-su-z0-9-]torrent/`**, dropping
`c`. Nothing in the 494 needs a `c` before `torrent`. `legittorrents.info` was already safe because
the class excludes `t`, and that exclusion is what also keeps `bittorrent.com` out.

Three exclusions in that class are load bearing and none of them is obvious:

- **no `t`** is what stops `bittorrent.com`.
- **no `c`** is what stops `academictorrents.com`.
- **no `.`** is what stops `www.torrentfreak.com` and `ipv6.torrent.ubuntu.com`.

Anyone who "simplifies" the class to `[^t]` or `.` reopens all three.

**The trade taken, so nobody reverts it by accident.** Excluding `t` has a structural reason
(`bittorrent`). Excluding `c` does not, it is there purely for `academictorrents.com`, and the cost
is that the class no longer catches a future `pctorrents` or `cinematorrents`. The alternative was
to keep `c` and add `@@/(^|\.)academictorrents\.com$/` as a third exception, which states the
intent more plainly at the cost of one more rule. Either is defensible; the narrower class was
chosen to keep the exception list down to the two rules that are genuinely load bearing. If a `c`
torrent brand shows up later, swap to the exception rather than widening the class blindly.

### 3. The tracker mega-pattern

Two separate problems, and the brief attributed one of them to the wrong pattern.

**`linuxtracker.org` was matched by the prefix pattern, not the mega-pattern.** The old
`/(^|[.-])(ru|re|open|...|linux|...)-?tracker/` had `linux` in its prefix list. Fixing the
mega-pattern would not have fixed this. `linux` is gone from the list, and so are `the`, `my`,
`best` and `hd`, which are ordinary English words that would happily match a company issue tracker
at `my-tracker.acme.com`.

**The mega-pattern itself** was 3000+ characters with a giant public-TLD alternation, and it still
missed `tracker.torrent.eu.org`, `tracker1.bt.moack.co.kr`, `tracker.ololosh.space` and
`tracker.tcp.exchange`. It is replaced, together with `/\.tracker\./` and
`/^tracker(turk|x|zone|[0-9])/`, by one line:

```
/(^|\.)tracker[0-9]?\./
```

Read it as: a whole label that is exactly `tracker`, or `tracker` plus one digit. That covers all 23
curated tracker hosts and all their subdomain variants, it is one line a human can read, and the
private-namespace exception rule handles `tracker.mycompany.internal` instead of a TLD allowlist.
Confirmed clean on the block rule alone: `linuxtracker.org`, `sbtracker.dev`,
`issue-tracker.example.com` and `bugtracker.corp.local` all have a letter or a hyphen immediately
before `tracker`, so none of them reaches a label boundary.

### 4. `/[a-z0-9]movie/` matched `themoviedb.org`

TMDB is the metadata API behind Jellyfin, Kodi, Radarr and Plex. It was also hitting
`api.themoviedb.org`, `www.themoviedb.org` and Google's `playmoviesdfe-pa.googleapis.com`.

The generic form is gone. It is replaced by two patterns, a brand list and a label-anchored shape:

```
/(^|[.-])(123|f|go|look|solar|vega|yes|bolly|hd|see|sock|prime|watch32)movies?/
/(^|[.-])movie(s[a-z0-9]|[a-eg-rt-z])/
```

The first covers `123movies`, `fmovies`, `gomovies`, `lookmovie`, `solarmovie`, `vegamovies`,
`yesmovies` and friends, and absorbs the old standalone `/fmovies/`. The second covers
`moviesjoy.plus` and `movieskiduniya.com` while excluding `moviefone.com` (the `f` is missing from
the class) and a bare `movies.com` (needs a letter or digit after the `s`). `themoviedb.org` and
`playmoviesdfe-pa.googleapis.com` both have a letter immediately before `movie`, so neither reaches
a label boundary.

### 5. `/^p2p/` (also asked for)

It was matching `p2p2.cloudbirds.cn` through `p2p6.cloudbirds.cn` and
`p2p-ord1.discovery.steamserver.net`, which is Steam. It covered exactly one curated domain. It is
now **`/(^|\.)p2p-world\./`**, which is the brand and keeps mirror coverage across TLD hops. A bare
`p2p-` prefix was deliberately avoided or Steam comes straight back.

---

## The rules

82 block patterns, then 2 exceptions. Counts are curated **base domains** out of 494; each one
implies six matched hostnames. "sole" is how many that pattern is the only one to cover.

| # | Pattern | What it covers | base | sole |
|---|---|---|---|---|
| 1 | `/(^\|[.-])(with)?youtube\./` | Every `youtube.<tld>`, all their subdomains, `withyoutube.com` and `wide-youtube.l.google.com`. `youtubei.googleapis.com` cannot match because a literal dot is required after `youtube`. | 154 | 154 |
| 2 | `/(^\|\.)youtube(kids\|gaming\|education\|fanfest\|go\|mobilesupport\|embeddedplayer\|-nocookie\|-ui)/` | YouTube sub-brands. | 14 | 14 |
| 3 | `/(^\|\.)(youtu\|yt)\.be$/` | The two short-link domains and their subdomains. | 2 | 2 |
| 4 | `/[a-bd-su-z0-9-]torrent/` | `torrent` preceded by a letter, digit or hyphen, but never `t` (blocks `bittorrent.com`), never `c` (blocks `academictorrents.com`), never `.`. | 17 | 16 |
| 5 | `/(^\|\.)torrent(fu\|[a-eg-z0-9-])/` | `torrent` starting a label, followed by anything but `fr`. Keeps `torrentfunk`, blocks `torrentfreak.com`. A following dot is excluded, so `torrent.ubuntu.com` and `torrent.fedoraproject.org` are safe. | 19 | 19 |
| 6 | `/[a-z]bittorrent/` | `openbittorrent`, `qbittorrent`. Needs a letter in front, so `bittorrent.com` and `www.bittorrent.com` cannot match. | 1 | 0 |
| 7 | `/(^\|\.)tracker[0-9]?\./` | A whole label that is `tracker` or `tracker<digit>`. Replaces three old patterns including the 3000-character one. | 23 | 21 |
| 8 | `/(^\|[.-])(ru\|re\|open\|public\|bal\|brown\|chronic\|kray\|nyaa\|aradi\|sub\|acg\|central\|turk\|z\|ayu\|greek\|metal\|mma\|spirit\|bt)-?tracker/` | Known tracker brand prefixes glued to `tracker`. `linux`, `the`, `my`, `best` and `hd` removed. | 6 | 6 |
| 9 | `/1337x\|1377x\|(^\|\.)1337\./` | The 1337x / 1377x mirror family. | 9 | 9 |
| 10 | `/(^\|\.)yts(proxies)?\./` | YTS and its proxy domain. `tracker.skyts.net` is safe, `yts` there follows a `k`. | 5 | 5 |
| 11 | `/yify/` | YIFY release group. | 0 | 0 |
| 12 | `/eztv/` | EZTV mirrors. | 7 | 7 |
| 13 | `/nyaa/` | Nyaa anime trackers. | 4 | 4 |
| 14 | `/kickass/` | KickassTorrents and kickassanime. | 3 | 2 |
| 15 | `/demonoid\|demonii/` | Demonoid and the demonii tracker. | 3 | 3 |
| 16 | `/pirate(bay\|proxy\|-bay\|browser\|iro\|club\|pc\|ic\|-share)/` | The Pirate Bay ecosystem. Bare `pirate` is not used. | 9 | 9 |
| 17 | `/rarbg\|rargb/` | RARBG, its mirrors and the `rargb` typo family. | 8 | 7 |
| 18 | `/soap2day\|soaper\./` | Soap2day and Soaper. | 5 | 5 |
| 19 | `/warez/` | Any hostname containing `warez`. | 0 | 0 |
| 20 | `/zooqle\|zoozle/` | Zooqle, Zoozle. | 2 | 2 |
| 21 | `/monova\|(bite\|bit\|dutch\|mini\|new)nova\|nova(hax\|mov)/` | The nova torrent family. | 1 | 1 |
| 22 | `/isohunt/` | IsoHunt. | 0 | 0 |
| 23 | `/magnetdl/` | MagnetDL. | 2 | 2 |
| 24 | `/avistaz\|exoticaz\|cinemaz/` | The AvistaZ private tracker network. | 3 | 3 |
| 25 | `/filelist/` | FileList. | 1 | 1 |
| 26 | `/(hd\|uhd\|sd\|he\|ccf\|fdd\|hdvn\|extreme\|power\|panthera\|nordic\|film\|porn\|learn)bits/` | The `<name>bits` private tracker family. Absorbs the old `/hdbits/`. `am` was dropped from the prefix list; `bc` was never in it, so `bcbits.com` (Bandcamp CDN) stays safe. | 2 | 2 |
| 27 | `/(^\|\.)ncore\./` | nCore, anchored to a label boundary. | 0 | 0 |
| 28 | `/knaben/` | Knaben. | 2 | 2 |
| 29 | `/(^\|\.)bt(4g\|arg\|bot\|db\|dig\|gigs\|junkie\|mon\|music\|r\.\|scene\|zone\|-)/` | `bt`-prefixed torrent brands. `c` is absent so `btcpayserver.org` cannot match. | 5 | 5 |
| 30 | `/(^\|\.)bt[0-9]\.[a-z0-9-]+\.[a-z]/` | `bt1.archive.org`, `bt2.archive.org` and their subdomains. A digit is now **required**, which is what keeps `abt.com`, `debt.com` and BT's own `bt.com` out. | 2 | 2 |
| 31 | `/9anime\|allanime\|anime-faith\|anime-legion\|animebw\|animeby\|animeflix\|animeforever\|animekai\|animela\|animeowl\|animepahe\|animesug\|animesuki\|c1anime\|downloadanime\|gogoanime\|hqanime/` | Known anime piracy brands. A bare `/anime/` would hit `myanimelist.net`. | 13 | 12 |
| 32 | `/crack(ed[a-z]\|[^e])/` | `crack` followed by anything but `e`, plus `cracked<letter>`. Keeps `crackerbarrel.com` and `nutcracker.org` out. | 2 | 2 |
| 33 | `/keygen/` | Keygen sites. | 0 | 0 |
| 34 | `/repack/` | Game repack sites. | 4 | 4 |
| 35 | `/skidrow/` | Skidrow releases. | 2 | 2 |
| 36 | `/(^\|[.-])(123\|f\|go\|look\|solar\|vega\|yes\|bolly\|hd\|see\|sock\|prime\|watch32)movies?/` | Movie piracy brands at a label or hyphen boundary. Replaces the old `[a-z0-9]movie` and absorbs `/fmovies/`. | 14 | 14 |
| 37 | `/(^\|[.-])movie(s[a-z0-9]\|[a-eg-rt-z])/` | `movie` starting a label, plus a letter. Excludes `moviefone` and a bare `movies.`. | 2 | 2 |
| 38 | `/serial(coded\|keys\|number\|portal\|start\|surf)/` | Warez `serial<word>` sites. The old loose `[a-z]serial` half was dropped. | 0 | 0 |
| 39 | `/(^\|\.)download(anime\|arch\|emule\|forum\|portal\|post\|space\|team\|top)/` | `download<word>` sites, word-list restricted so `download.microsoft.com` cannot match. | 0 | 0 |
| 40 | `/scene(hd\|spot\|time\|x\.\|-rush)\|thescene\|datascene\|prescene/` | Warez scene sites. A bare `/scene/` would hit `scene7.com`. | 1 | 1 |
| 41 | `/[a-z]flix\.\|(^\|\.)flix(dump\|flux\|hq\|tor)\|myflixer/` | `flix` streaming brands. `flixster.com` cannot match. | 7 | 6 |
| 42 | `/manga(dex\|fire\|go\|kakalot\|nato\|park)\|natomanga/` | Manga piracy readers. | 7 | 7 |
| 43 | `/(^\|\.)kino(-hit\|club\|mall\|mix\|mob\|x\.\|zal)/` | Russian kino streaming, word-list restricted so `kino.de` and `kinopoisk.ru` are safe. | 1 | 1 |
| 44 | `/arenabg/` | ArenaBG and its p4p tracker hosts. | 1 | 1 |
| 45 | `/(^\|\.)hd(club\|china\|city\|dvdrip\|road\|source\|star\|bt\.)/` | `hd`-prefixed private tracker brands. The bare `-` branch was **removed**; it was matching `hd-personalization-prod.gcp.homedepot.com`. | 0 | 0 |
| 46 | `/(^\|\.)(kat\.cr\|katcr\.\|katz\|thekat\.)/` | Kickass Torrents `kat.*` mirrors. | 2 | 2 |
| 47 | `/(^\|\.)p2p-world\./` | p2p-world across TLDs. Replaces `/^p2p/`. | 1 | 1 |
| 48 | `/(^\|\.)nnm(club\|-club)/` | NNM-Club. Replaces the looser `/^nnm/`. | 1 | 1 |
| 49 | `/putlocker/` | Putlocker mirrors. | 2 | 2 |
| 50 | `/unblocked/` | `unblocked` proxy domains. | 0 | 0 |
| 51 | `/streameast\|streamzone/` | StreamEast, StreamZone. | 3 | 3 |
| 52 | `/hesgoal\|totalsportek/` | HesGoal, TotalSportek. | 4 | 4 |
| 53 | `/hianime\|zorox?\.\|hurawatch/` | HiAnime, Zoro, HuraWatch. | 7 | 7 |
| 54 | `/rutor/` | Rutor. | 3 | 3 |
| 55 | `/audiobookbay\|(^\|\.)ebook(directory\|share\|vortex)/` | AudioBookBay and ebook piracy. | 0 | 0 |
| 56 | `/blackcats-games\|blackhatprotools/` | BlackCats-Games, BlackHatProTools. | 0 | 0 |
| 57 | `/passthepopcorn/` | PassThePopcorn. | 1 | 1 |
| 58 | `/primewire/` | PrimeWire. | 1 | 1 |
| 59 | `/secret-cinema/` | Secret-Cinema. | 1 | 1 |
| 60 | `/sportsurge/` | SportSurge. | 2 | 2 |
| 61 | `/mvgroup/` | MVGroup. | 0 | 0 |
| 62 | `/nsanedown/` | nsanedown. | 0 | 0 |
| 63 | `/(^\|[.-])(watch\|tv\|top\|mega\|see\|hd\|full)series/` | `<word>series` streaming brands. Replaces the old bare `[a-z]series`. | 2 | 2 |
| 64 | `/ettv/` | ETTV release group. | 2 | 2 |
| 65 | `/torlock/` | TorLock. | 2 | 2 |
| 66 | `/daddylive/` | DaddyLive. | 2 | 2 |
| 67 | `/cric(free\|hd\|stream)/` | Cricket streaming piracy. A bare `/cric/` would hit `cricbuzz.com`. | 3 | 3 |
| 68 | `/(^\|\.)livetv[0-9.]/` | LiveTV sports mirrors. | 2 | 2 |
| 69 | `/rojadirecta/` | RojaDirecta. | 2 | 2 |
| 70 | `/elamigos/` | ElAmigos game repacks. | 2 | 2 |
| 71 | `/igg-?games/` | IGG-Games. | 2 | 2 |
| 72 | `/(^\|\.)ps[45]pkg/` | PlayStation pkg/ROM sites. | 0 | 0 |
| 73 | `/(^\|\.)hit[24]k/` | hit2k, hit4k warez. | 0 | 0 |
| 74 | `/(^\|\.)ani(db\|dex\|rena\|playnow\|taku\|watch)/` | `ani`-prefixed anime piracy brands. | 3 | 3 |
| 75 | `/hentai/` | hentai sites. | 3 | 3 |
| 76 | `/(^\|[.-])kiss(asian\|anime\|cartoon\|kh\|manga)/` | **New.** The Kiss* streaming family, which domain-hops constantly. | 2 | 2 |
| 77 | `/(^\|[.-])(apunka\|oceanof\|ova\|worldofpc\|gazelle)games/` | **New.** Cracked-game download brands. Replaces the old generic `[a-z0-9]-games\.`. | 5 | 5 |
| 78 | `/hiddenbay\|(^\|[.-])proxybay\|(^\|\.)tpb\./` | **New.** Pirate Bay proxy and mirror brands. | 3 | 3 |
| 79 | `/(^\|[.-])xtr(ea\|e)me?(-codes\|bytes\|hd)/` | **New.** Xtream-Codes IPTV piracy family. | 3 | 3 |
| 80 | `/(^\|[.-])vip(box\|league\|row)/` | **New.** VIPBox / VIPLeague sports streaming. | 2 | 2 |
| 81 | `/(^\|[.-])bit(search\|porn)/` | **New.** BitSearch, BitPorn. | 2 | 2 |
| 82 | `/torrends/` | **New.** Torrends, a torrent aggregator whose spelling dodges every `torrent` pattern. | 1 | 1 |
| E1 | `@@/(^\|\.)music\.youtube\.com$/` | Exception. Keeps YouTube Music working. | - | - |
| E2 | `@@/\.(internal\|local\|corp\|lan\|home\|intranet)$/` | Exception. Never block a private namespace. | - | - |

---

## Summary

- **Misses: 0.** "Miss" means a base domain that no pattern matches *and* that is not in
  `leftover_literals.txt`. Every one of the 494 ends up blocked, either by a regex or by its
  literal rule.
- **82 block patterns + 2 exception rules.** The two `@@` lines live in `regexes.txt` on purpose,
  grouped at the bottom. That is a deliberate deviation from "one `/pattern/` per line": splitting
  them into a second file means anyone who loads `regexes.txt` alone blocks `music.youtube.com`.
- **64 leftover literals** in `leftover_literals.txt`
- 430 of the 494 curated base domains are fully covered by regex, meaning all six hostname variants
  of each. 64 fall to literal rules.
- At hostname level: **2580 of the 2964** expanded hostnames match a regex. The other 384 are the
  six variants each of the 64 literals and are covered by their `||domain^` rules.
- Rule count goes from 494 literals to 82 + 2 + 64 = **148 rules**.

### Go verifier results

Verifier at `/tmp/rgxverify/v2/main.go`, Go 1.25.6, standard-library `regexp` (RE2). Run with:

```
./v2 /tmp/rgx/regexes.txt \
     /tmp/rgx/must_cover_curated.txt \
     /tmp/rgxverify/must_cover_subdomains.txt \
     /tmp/rgx/guard3.txt \
     /tmp/rgxverify/top20k.txt \
     /tmp/rgx/keep_literal.txt \
     /tmp/rgx/leftover_literals.txt
```

```
== RE2 compile: 82 block + 2 exception rules, 0 failures
== expansion sanity: 494 base x 6 prefixes = 2964; 0 not present in expanded file (file has 2964)
== exceptions vs targets: 0 violations (must be 0)
== base domains: 494 total | 430 fully regex-covered | 0 partial (BUG) | 64 left as literals
== base domains not covered by regex and NOT in leftover_literals: 0
== hostname coverage over 2964 expanded targets: 2580 matched by regex, 384 fall to literal rules
== guard: 2 raw block hits, 0 effective hits after exceptions (must be 0)
== top20k collateral scan: 16 unintended matches over 20000 domains
== 15 block patterns match nothing in the 494

SUMMARY block=82 exceptions=2 compilefails=0 partial=0 uncovered=0 guard_effective=0 collateral=16 literals=64
```

What each assertion means, since three of them are new this run:

1. **Every rule compiles with `regexp.MustCompile`.** That is the RE2 proof: no lookaheads, no
   lookbehinds, no backreferences. Python `re` was not used anywhere, because it accepts lookaheads
   that RE2 rejects.
2. **Exceptions apply to coverage, not just to guards.** A hostname counts as covered only if a
   block pattern matches it *and* no exception rescues it. Without this a sloppy exception could gut
   coverage and the number would still look green.
3. **No exception matches any of the 2964 targets.** Asserted directly. 0 violations.
4. **Coverage is measured per base domain, not per line.** All six variants covered, or the domain
   goes to literals. A domain where the apex matches but `www.` does not is reported as `PARTIAL`
   and counted as a bug. There are **0 partials**. That is the exact class of bug the previous run
   shipped.
5. **Guard hits are printed twice**, raw and after exceptions. Raw is 2, effective is **0**. A naive
   verifier that ignores exceptions will show `music.youtube.com` and `tracker.mycompany.internal`
   lighting up; that is expected and correct.

### Guard list: 0 effective hits

```
guard rescued by exception: music.youtube.com           block=/(^|[.-])(with)?youtube\./  exc=@@/(^|\.)music\.youtube\.com$/
guard rescued by exception: tracker.mycompany.internal  block=/(^|\.)tracker[0-9]?\./     exc=@@/\.(internal|local|corp|lan|home|intranet)$/
== guard: 2 raw block hits, 0 effective hits after exceptions
```

All four reported false positives are gone, verified individually:
`encore.scdn.co`, `academictorrents.com`, `www.academictorrents.com`, `legittorrents.info`,
`linuxtracker.org`, `themoviedb.org`, `api.themoviedb.org`, `image.tmdb.org`, plus every one of
`thetvdb.com`, `musicbrainz.org`, `trakt.tv`, `imdb.com`, `letterboxd.com`, `justwatch.com`,
`opensubtitles.com`, `scdn.co`, `spotifycdn.com` and the other Spotify CDN hosts.

---

## Top 20k collateral: all 16 hits, with a call on each

**Verdict: ship it. None of these breaks anything a normal person uses.**

### Ad-tech tracker endpoints (10 hits) — desirable

```
tracker.adex-rtb.com
tracker.ads-tinyorbit.com
tracker.cbx-rtb.com
tracker.direct.e-volution.ai
tracker.exchange.amitydigital.io
tracker.iionads.com
tracker.rtb-oveeo.com
tracker.rtb-stellormedia.com
tracker.samplicio.us
tracker.ssp.balance-x.com
```

All from `/(^|\.)tracker[0-9]?\./`. Every one is a real-time-bidding, supply-side-platform or
survey-panel endpoint. `rtb` means real-time bidding, `ssp` means supply-side platform. Blocking
these is a bonus, not damage. Nobody loses a feature.

There were 4 such hits before and there are 10 now, because widening `^tracker\.` to
`(^|\.)tracker\.` also reaches the `tracker.<label>.<domain>` form. All 6 new ones are the same kind
of host.

**Residual risk, stated plainly:** a company that runs a public issue tracker at
`tracker.<company>.com` gets blocked. `.internal`, `.local`, `.corp`, `.lan`, `.home` and
`.intranet` are protected by exception E2, so the private case is handled. The public case is a real
if unlikely cost, and it is the price of covering the single most valuable shape in a BitTorrent
blocklist. Drop pattern 7 and move its 23 hosts to literals if that trade is unacceptable.

### Netflix Akamai edge (2 hits) — consistent, not collateral

```
netflix.com.edgesuite.net
dscg.netflix.com.edgesuite.net
```

From `/[a-z]flix\./`. These are Netflix's Akamai edge hostnames. `netflix.com` is already on the
blocklist deliberately as a literal in `keep_literal.txt`, so blocking its CDN is the same decision,
not a new one. Called out here because it looks alarming in a raw hit list. If Netflix is ever
removed from the blocklist, this pattern has to be narrowed at the same time.

### One more consistent-not-collateral case, suppressed by the filter

`crackle.com`, Sony's free streaming service, matches `/crack(ed[a-z]|[^e])/`. It does not appear in
the 16 above because the verifier filters out anything already on the blocklist, and `crackle.com`
is in `keep_literal.txt`. Same situation as the Netflix edge hosts: consistent with a decision
already made, not new damage. Same warning too. If `crackle.com` ever comes off the blocklist, this
pattern must be narrowed at the same time.

### warez brand (4 hits) — desirable

```
wareztv.io
api1.wareztv.io
guard.wareztv.io
update.wareztv.io
```

From `/eztv/`, which matches the `eztv` inside war**eztv**. Accidental but correct: this is a warez
brand and it is exactly what the list is for. It is also caught by `/warez/`, which is a good reason
to keep `/warez/` despite it covering nothing in the current 494.

### Gone since the previous run

Eight hits the old set produced and this one does not:

| Was hit | By | Now |
|---|---|---|
| `themoviedb.org`, `www.themoviedb.org` | `[a-z0-9]movie` | fixed |
| `playmoviesdfe-pa.googleapis.com` (Google Play Movies) | `[a-z0-9]movie` | fixed |
| `encore.scdn.co` (Spotify CDN) | `ncore\.` | fixed |
| `screencore.io`, `cs.screencore.io` | `ncore\.` | fixed |
| `p2p2/3/5/6.cloudbirds.cn` | `^p2p` | fixed |
| `p2p-ord1.discovery.steamserver.net` (Steam) | `^p2p` | fixed |
| `hd-personalization-prod.gcp.homedepot.com` (Home Depot) | `^hd(-\|...)` | fixed |
| `dle-cdn.mheducation.com` (McGraw Hill) | `^dle-` | pattern dropped |

---

## Patterns dropped, with reasons

| Dropped | Reason |
|---|---|
| `/torrents/` | Sole coverage was zero and it matched `academictorrents.com` and `legittorrents.info`. |
| `/^tracker[0-9]?\.(150-TLD alternation)$/` | Replaced by `/(^\|\.)tracker[0-9]?\./`, which is shorter, readable, and covers four hosts the old one missed. |
| `/\.tracker\./` | Merged into the same pattern. |
| `/^tracker(turk\|x\|zone\|[0-9])/` | Merged. The `turk\|x\|zone` tail covered nothing and `trackerx` is a plausible product name. |
| `/fmovies/` | Absorbed into the movie brand list. |
| `/hdbits/` | Absorbed into the `<name>bits` pattern. |
| `/[a-z0-9]movie/` | Matched `themoviedb.org` and `playmoviesdfe-pa.googleapis.com`. Replaced by two tighter patterns. |
| the `[a-z]serial` half of the serial pattern | Loose, zero coverage. The word-list half stays. |
| `/[a-z0-9]-games\./` | Sole coverage zero, and `<word>-games` is ordinary English. Replaced by a brand list. |
| `/^bittorrent\.[a-z0-9-]+\.[a-z]+$\|frozen-layer/` | Zero coverage, and confusing to sit next to the `bittorrent.com` guard entry. |
| `/dnf24\|online-life\|primartists\|sweet-paris\|torfinder/` | Zero coverage, and `sweet-paris` is a real creperie chain while `online-life` is generic. |
| `/^dle-/` | Zero coverage and it was blocking `dle-cdn.mheducation.com`. Textbook "zero value, carries risk". |
| `/divx/` | Zero coverage and DivX is a legitimate codec company at `divx.com`. |
| `/^p2p/` | Replaced by the brand form. |
| `/^nnm/` | Replaced by `/(^\|\.)nnm(club\|-club)/`. |
| `/(^\|\.)mp3[a-z-]/` | Zero coverage and it would block `mp3tag.de`, a well-known legitimate tagging tool. |
| `/ehho/`, `/pow7\.com$/`, `/getlink\.vn$/`, `/file\.l[uv]$/`, `/acg\.rip$/` | Each pins one exact domain from the deleted extended list. They cannot even follow a TLD hop, so they carry no future-proofing value at all. |

Narrowed rather than dropped: `linux`, `the`, `my`, `best` and `hd` removed from the tracker prefix
list; `am` removed from the `bits` prefix list; the bare `-` and `log` branches removed from the
`hd` brand pattern; `c` removed from the torrent character class; `[0-9]?` tightened to `[0-9]` in
the `bt<digit>.` pattern.

## Patterns kept despite covering nothing in the 494

Fifteen patterns match none of the current 494. All are kept deliberately: each names a piracy brand
or a warez shape that reappears under a new TLD every few months, and that mirror-catching is the
main reason to use regexes instead of a literal list at all. None of them hits anything in the top
20k or in the guard list.

`/yify/`, `/warez/`, `/isohunt/`, `/(^|\.)ncore\./`, `/keygen/`,
`/serial(coded|keys|number|portal|start|surf)/`, `/(^|\.)download(anime|arch|...)/`,
`/(^|\.)hd(club|china|city|dvdrip|road|source|star|bt\.)/`, `/unblocked/`,
`/audiobookbay|(^|\.)ebook(directory|share|vortex)/`, `/blackcats-games|blackhatprotools/`,
`/mvgroup/`, `/nsanedown/`, `/(^|\.)ps[45]pkg/`, `/(^|\.)hit[24]k/`.

## The 64 leftover literals

These are one-off brands with no shared token any safe regex can key on: `aither.cc`, `blutopia.cc`,
`milkie.cc`, `orpheus.network`, `redacted.ch`, `myanonamouse.net`, `snowfl.com`, `gtdb.to`,
`glodls.to`, `idope.top` and the like. Most are invite-only private trackers with a single stable
domain, where a `||domain^` literal is the right tool anyway. Several have names that are ordinary
words in another language (`comando.la`, `lapumia.net`, `descargas2020.org`), and one,
`iptv-org.github.io`, sits on GitHub Pages, where any regex broad enough to catch it would catch all
of `github.io`.

Full list in `/tmp/rgx/leftover_literals.txt`.

## Tempting patterns that were rejected

- Bare `/anime/`: hits `myanimelist.net` and `animenewsnetwork.com`.
- Bare `/movie/`: hits `themoviedb.org`, the metadata API behind Jellyfin, Kodi, Radarr and Plex.
- Bare `/torrents/`: hits `academictorrents.com` and `legittorrents.info`.
- Bare `/scene/`: hits `scene7.com`, Adobe's image delivery host.
- Bare `/download/`: hits `download.microsoft.com` and `downloads.apache.org`.
- Bare `/games/`: hits `epicgames.com`.
- Bare `/^hd/`: hits `hdfcbank.com` and Home Depot.
- Bare `/bits\./`: hits `bcbits.com`, the Bandcamp CDN.
- Bare `/^bit[a-z]/`: hits `bitwarden.com`, `bitdefender.com`, `bitbucket.org`.
- Bare `/^cric/`: hits `cricbuzz.com`.
- Bare `/serial/`: hits `serialport.io`.
- Bare `/p2p-/`: hits `p2p-ord1.discovery.steamserver.net`, which is Steam.
- Bare `/mp3[a-z]/`: hits `mp3tag.de`.
- `/(^|\.)torrent\./`: three guard entries are exactly that shape (`torrent.ubuntu.com`,
  `torrent.fedoraproject.org`, `ipv6.torrent.ubuntu.com`).
- A known-public-TLD alternation on `tracker.`: 3000 characters, unmaintainable, and it still missed
  `.space`, `.exchange` and multi-label hosts. Replaced by a one-line pattern plus one global
  exception for private namespaces.
