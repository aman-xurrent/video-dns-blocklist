# Video Entertainment and Torrent DNS Blocklist

A DNS level blocklist that kills video entertainment and torrents, and leaves music alone.

The line is drawn at video, not at entertainment in general. **Anything you watch is blocked.
Anything you only listen to is not.** Spotify, Apple Music, Amazon Music and YouTube Music all
keep working.

Written in AdGuard DNS filtering syntax, the same syntax the
[AdGuard DNS filter](https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt) uses.

## Subscribe

Two builds, same coverage. Pick one.

**Compact, 485 rules.** Use this if your resolver caps you. The AdGuard DNS Personal plan
allows 1000 filtering rules, and that cap applies to **custom blocklists added by URL**, which
is exactly how you would subscribe to this one. AdGuard's own catalog lists do not count against
it, so enabling the AdGuard DNS filter alongside this costs you nothing. Go over the cap and the
offending custom list is disabled automatically. Team is 5K, Enterprise is 100K.

```
https://raw.githubusercontent.com/aman-xurrent/video-dns-blocklist/main/filter-compact.txt
```

**Full, 790 rules.** Every rule is a plain domain, nothing to reason about. Use this if you
self host AdGuard Home or Pi-hole, where there is no cap.

```
https://raw.githubusercontent.com/aman-xurrent/video-dns-blocklist/main/filter.txt
```

The compact build swaps 494 literal domain rules for 123 regular expressions. It is not just
smaller: a brand anchored pattern like the one covering 1337x follows that site to whatever TLD
it jumps to next month, which a literal list cannot do.

Both are validated with
[`@adguard/hostlist-compiler`](https://github.com/AdguardTeam/HostlistCompiler) v2.1.1 (zero
invalid rules, zero duplicates) and tested against AdGuard's own matching engine,
[`urlfilter`](https://github.com/AdguardTeam/urlfilter): 2964 hostnames must block and all do,
129 guard hostnames must stay reachable and all do.

| Resolver | How to add it |
|---|---|
| AdGuard Home | Filters > DNS blocklists > Add blocklist. Both rule types work as is. |
| AdGuard DNS | Custom blocklist URL, or paste into custom filtering rules. |
| Pi-hole | Use `filter.txt`, not the compact build: Pi-hole does not evaluate regex rules from an adlist. Adlists also do **not** reliably understand `@@` exceptions, so add `music.youtube.com` to Domains > Allow by hand. |
| NextDNS | Denylist import, then allow `music.youtube.com` by hand. |

## What it blocks

**Video streaming.** YouTube, Netflix, Prime Video, Disney+ and JioHotstar, Max, Hulu,
Paramount+, Peacock, Apple TV+, Crunchyroll, SonyLIV, Zee5, MX Player, Tubi, Pluto and the rest,
including their video CDNs.

**Live, creator and short video.** Twitch, Kick, Rumble, TikTok, Dailymotion, Vimeo, Bilibili.

**Torrents.** Index sites, the public tracker announce hosts, and cloud torrent and debrid
services: webtor.io, Seedr, Bitport, ZbigZ, put.io, Offcloud, Premiumize, Real-Debrid, AllDebrid,
TorBox, Stremio.

**Unlicensed streaming.** Pirate movie and TV sites, live sports restreams, IPTV panels, anime and
manga readers, game repack sites.

**MEGA and Plex**, by explicit request rather than by the video rule.

## What it does not block

Every music service. Spotify, Apple Music, Amazon Music, YouTube Music, SoundCloud, Deezer, Tidal,
Pandora, JioSaavn, Gaana, Wynk, Bandcamp, Last.fm, Qobuz and Anghami are all named one by one in
the allowlist at the bottom of `filter.txt`, so the intent survives you merging this with someone
else's blocklist.

Also left alone on purpose: `amazon.com`, `apple.com`, `google.com`, `googleapis.com`,
`amazonaws.com`, `archive.org`, the Ubuntu and Fedora torrent trackers, Jellyfin and Emby, and
general cloud storage like Google Drive, Dropbox and OneDrive.

## Read this before you file a bug

### YouTube Music works, but signing in does not

YouTube and YouTube Music are not separate services underneath. They share a backend. These stay
unblocked on purpose because Music needs them: `googlevideo.com`, `youtubei.googleapis.com`,
`ytimg.com`, `ggpht.com`, `googleusercontent.com`.

Two consequences:

1. **The native YouTube app still plays video.** On Android, iOS and smart TVs it talks to
   `youtubei.googleapis.com` and `googlevideo.com` and never resolves `youtube.com`. What this
   list does kill is YouTube on the web, on every device on your network. DNS cannot do better
   than that. If you need the apps gone, remove them from the device or use an MDM app block.

2. **Signing in to YouTube Music in a browser breaks.** The sign-in link hands Google a continue
   URL of `https://www.youtube.com/signin?...`, and that hostname is blocked. If you are already
   signed in, nothing happens. To sign in fresh, do one of these:
   - sign in on the YouTube Music phone app, which never touches `www.youtube.com`, or
   - pause the filter, sign in once, turn it back on, or
   - temporarily add `@@||www.youtube.com^`, sign in, remove it.

Playback, search and your library all work fine once you are signed in. Verified on 2026-08-28 by
reading the real `music.youtube.com` HTML: the player JavaScript is served from `/s/player/` on
its own hostname and the InnerTube API call is same origin.

### Strict tier

Uncomment `||youtubei.googleapis.com^` in the header to also kill the native YouTube app **and**
the native YouTube Music app. The YouTube Music web player keeps working, because on the web
InnerTube is same origin and audio still comes from `googlevideo.com`. So: music in a browser
only, no YouTube app at all.

Never uncomment `||googlevideo.com^`, `||ytimg.com^` or `||ggpht.com^`. Those break YouTube Music
completely.

### Plex blocks your own server too

`plex.direct` is the hostname Plex apps use to reach a server on your own LAN, so blocking it
stops local playback, not just Plex sign-in. Delete that one line if you run your own server and
only want the Plex service blocked.

### One residual risk in the compact build

`/(^|\.)tracker[0-9]?\./` blocks any hostname whose first label is `tracker`. That is what
collapses 71 announce hosts into one rule, and it also catches ad tech endpoints like
`tracker.samplicio.us`, which you probably want. But if your employer runs a public issue tracker
at `tracker.company.com`, it gets blocked. Private namespaces are protected by an exception rule
covering `.internal`, `.local`, `.corp`, `.lan`, `.home` and `.intranet`. Public ones are not.
Use `filter.txt` if that matters to you.

### YouTube description links die

`youtube.com/redirect` is the hop every link in a YouTube video description goes through, and it
is part of `youtube.com`. Same for `youtu.be` short links anyone sends you. Expected, not a bug.

## How it was built

Every domain was resolved against 1.1.1.1 and cross checked against 8.8.8.8 on 2026-08-28.

- Anything that answered NXDOMAIN was dropped. That killed 123 candidates, including `yts.mx`,
  `primewire.mx`, `methstreams.com` and `idope.se`, all of which are genuinely gone.
- Anything resolving to a known domain parking IP was dropped.
- Domains with no A record at the apex but a live DNS zone were **kept**, because that is normal
  for CDN parents like `nflxso.net`, `hdslb.com` and `aiv-cdn.net` where all the traffic sits on
  subdomains. Dropping those on a failed A lookup would have silently gutted the list.

### What v1.0 and v1.1 got wrong

Those versions carried an extra 1148 domains imported from The Block List Project. Every one had
been DNS resolved, which proved they were alive. It did not prove they were piracy sites, and
that turned out to matter. Sitting in that block were:

```
nasa.gov   worldwind.arc.nasa.gov   gutenberg.org
webcast.berkeley.edu   pbs.org   bittorrent.com
```

All six are legitimate. Each is on a torrent blocklist because it once ran a BitTorrent tracker
to hand out something lawful: NASA satellite imagery, Project Gutenberg ebooks, Berkeley lecture
recordings. The other 1142 could not be checked by hand with any confidence, so the whole block
was dropped in v1.2.0 rather than shipped on trust. Coverage of the genuinely piracy shaped
domains now comes from regular expressions that match on brand and shape.

### Two engine behaviours that break naive regex compression

Both found by testing AdGuard's real engine rather than reading the docs. Both are written up in
`tools/verify/README.md` with runnable reproductions.

**Regex rules do not match subdomains.** `||1337x.to^` covers `www.1337x.to`. `/^1337x\./` does
not. An early draft leaked 1469 of 2964 hostnames to this.

**Top level alternation silently half works.** The engine indexes each rule by one literal
substring pulled from the pattern, so only the first branch is ever reachable:

```
/1377x/         1377x.to -> blocked
/1337x|1377x/   1377x.to -> NOT BLOCKED
/1337x|1377x/   1337x.to -> blocked
```

`build_compact.py` splits top level alternation automatically for this reason.

## Refreshing it

Piracy mirror domains rotate every few weeks. The torrent and pirate streaming sections need a
refresh every month or two. The licensed streaming section is stable and does not.

```sh
# edit the source lists in tools/, then
python3 tools/build.py                 # regenerates filter.txt
python3 tools/build_compact.py         # regenerates filter-compact.txt, fails if over 1000

npx @adguard/hostlist-compiler -c tools/cfg.json -o /dev/null
npx @adguard/hostlist-compiler -c tools/cfg-compact.json -o /dev/null

cd tools/verify && go run accept.go ../../filter-compact.txt   # real engine check
```

`tools/build.py` regenerates `filter.txt` byte for byte from `tools/header.txt`,
`tools/footer.txt` and the `tools/cur_*.txt` source lists. `tools/digsweep.sh` and
`tools/digns.sh` are the liveness probes described above.

## Credits and license

The YouTube country domain list came from
[v2fly/domain-list-community](https://github.com/v2fly/domain-list-community). Earlier versions
also drew on [The Block List Project](https://github.com/blocklistproject/Lists); that section was
removed in v1.2.0 for the reasons above.

Everything else in this repo is MIT licensed. See [LICENSE](LICENSE).

This is a self control tool. It is not a security product, it does not stop anyone who is trying
to get around it, and blocking a domain says nothing about whether that site is legal where you
live.
