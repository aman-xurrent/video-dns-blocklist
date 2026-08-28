# Video Entertainment and Torrent DNS Blocklist

A DNS level blocklist that kills video entertainment and torrents, and leaves music alone.

The line is drawn at video, not at entertainment in general. **Anything you watch is blocked.
Anything you only listen to is not.** Spotify, Apple Music, Amazon Music and YouTube Music all
keep working.

Written in AdGuard DNS filtering syntax, the same syntax the
[AdGuard DNS filter](https://adguardteam.github.io/AdGuardSDNSFilter/Filters/filter.txt) uses.

## Subscribe

```
https://raw.githubusercontent.com/aman-xurrent/video-dns-blocklist/main/blocklist.txt
```

493 rules: 126 regular expressions, 330 literal domains, 37 exceptions.

> **Renamed in v1.3.1.** This file used to be `filter-compact.txt`. It was renamed to bust a
> stale cache, since AdGuard and the GitHub raw CDN both cache by URL. One time only. Future
> content updates land at this same URL and refresh on their own.

The AdGuard DNS Personal plan allows 1000 filtering rules, and that cap applies to **custom
blocklists added by URL**, which is how you subscribe to this. AdGuard's own catalog lists do not
count against it, so enabling the AdGuard DNS filter alongside this costs you nothing. A custom
list that goes over the cap is disabled automatically. Team is 5K, Enterprise is 100K.

Validated with [`@adguard/hostlist-compiler`](https://github.com/AdguardTeam/HostlistCompiler)
v2.1.1 (zero invalid rules, zero duplicates) and tested against AdGuard's own matching engine,
[`urlfilter`](https://github.com/AdguardTeam/urlfilter): 2964 hostnames must block and all do,
128 guard hostnames must stay reachable and all do.

| Resolver | How to add it |
|---|---|
| AdGuard Home | Filters > DNS blocklists > Add blocklist. |
| AdGuard DNS | Custom blocklist URL, or paste into custom filtering rules. |
| NextDNS | Denylist import, then allow `music.youtube.com` by hand. |
| Pi-hole | **Not supported as is.** See below. |

### Pi-hole needs a different build

Pi-hole cannot read regular expressions from an adlist. It parses `||domain^` fine, but `/regex/`
entries are ignored, so this file would silently degrade to its 330 literal rules and lose the
piracy brand coverage. Pi-hole also ignores `@@` exceptions.

There used to be a second all-literal `blocklist-full.txt` in this repo for that case. It was
deleted because the compact build is a strict superset of it (verified: 4560 hostnames blocked by
the literal build, zero missed by the compact one) and keeping two outputs in sync caused real
bugs. Nothing is lost, because the literal build is generated, not hand written:

```sh
python3 tools/build.py     # writes blocklist-full.txt
```

Then host that file yourself and add `music.youtube.com` to Pi-hole's allow list by hand.

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
the allowlist at the bottom of `blocklist.txt`, so the intent survives you merging this with someone
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

### Strict tier, on by default since v1.3.0

`||youtubei.googleapis.com^` is an active rule. It kills **both** native apps, YouTube and
YouTube Music, because both talk to the private InnerTube API and nothing else reaches it.

**YouTube Music in a browser still works.** Verified in a live session, not assumed: every
InnerTube call the web player makes goes same origin to `music.youtube.com/youtubei/v1/`
(player, next, browse, guide, search suggestions) and audio streams from `googlevideo.com`. It
never touches `youtubei.googleapis.com`.

To go back to the softer behaviour where the apps work, delete that rule and add
`@@||youtubei.googleapis.com^` to the allowlist.

Never block `googlevideo.com`, `ytimg.com` or `ggpht.com`. Those break YouTube Music on the web
too.

### Why you cannot block the video but keep the audio

This gets asked a lot, so here is the measurement. Reading the live player response for three
tracks on 2026-08-28:

| track | audio host | video host |
|---|---|---|
| Never Gonna Give You Up | `rr5---sn-ci5gup-cagee` | `rr5---sn-ci5gup-cagee` |
| Together Forever (remaster) | `rr3---sn-ci5gup-cagee` | `rr3---sn-ci5gup-cagee` |
| Together Forever (art track) | `rr8---sn-ci5gup-cagr` | `rr8---sn-ci5gup-cagr` |

Audio and video for the same track come from the **identical hostname**, every time. The only
difference is the `itag` and `mime` query parameters, and DNS never sees a query string. The host
is also allocated per request, which is why the replica number moves between `rr3`, `rr5` and
`rr8` within a single session, so there is nothing stable to key on either.

Even a YouTube Music art track, the thing Song mode plays, carries 13 video formats. An art track
*is* a video: a still image encoded as video with the audio muxed alongside. Song mode is the
client picking an audio itag from the same manifest on the same host, not a different stream.

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
If that bites you, delete the `/(^|\.)tracker[0-9]?\./` line and you lose nothing else.

### Native apps

The streaming sections are written as domains, and `||domain^` covers every subdomain, so the
native **Netflix, Prime Video, JioHotstar, Disney+, SonyLIV, Zee5, Max, Hulu, Crunchyroll and
Twitch** apps are already blocked. Verified against the hostnames those apps actually call.

Three gaps needed explicit rules, and they are in the "Native mobile and TV app endpoints"
section:

1. **Apple TV+ was wide open because of this list's own allowlist.** Apple Music needs
   `itunes.apple.com`, so that domain is allowlisted, and the Apple TV+ app talks to `uts-api`,
   `play-edge` and `hls-svod` on exactly that domain. Those three now carry `$important`, which
   makes a block rule outrank an exception. Apple Music's `audio-ssl.itunes.apple.com` still
   works.
2. **Video hosts on shared CDNs.** `hses*.akamaized.net` is Hotstar, `avod*-a.akamaihd.net` is
   Prime Video. Only brand scoped names are touched. Bare `akamaized.net` and `akamaihd.net`
   serve thousands of unrelated sites and are left alone.
3. **`peacock.tv`**, which is a different domain from `peacocktv.com`.

Deliberately not blocked: `unagi.amazon.com` and friends. That is Prime Video telemetry, but the
Amazon shopping app uses it too, and blocking telemetry does not stop playback.

**The YouTube app is blocked since v1.3.0**, via `||youtubei.googleapis.com^`. The cost is that
the YouTube Music app dies with it, since they share that API. YouTube Music in a browser is
unaffected.

### If it blocks in the browser but not in apps

That is not a list problem, it is a setup problem. On iOS, AdGuard runs two separate protections:
Safari content blockers, which cover Safari only including private windows, and DNS protection,
which covers everything. Add this list under **DNS protection > DNS filters**, not under Safari
filters. The give away is that Netflix keeps playing in its app: every hostname that app uses is
on this list, so if it still works, DNS filtering is not reaching your apps.

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
python3 tools/build.py                 # regenerates blocklist-full.txt
python3 tools/build_compact.py         # regenerates blocklist.txt, fails if over 1000

npx @adguard/hostlist-compiler -c tools/cfg.json -o /dev/null
npx @adguard/hostlist-compiler -c tools/cfg-compact.json -o /dev/null

cd tools/verify && go run accept.go ../../blocklist.txt   # real engine check
```

`tools/build.py` regenerates `blocklist-full.txt` byte for byte from `tools/header.txt`,
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
