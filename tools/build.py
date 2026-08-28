import datetime, os

import os
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
def t(n): return os.path.join(HERE, n)
KEEP = set(open(t('curated_keep.txt')).read().split())
NOTES = {
 "YouTube: web front ends, country domains and brand properties":
   ["Blocks the YouTube web site in every country domain Google runs, plus Shorts, Kids,",
    "Gaming and the embed players. music.youtube.com is put back with an exception rule",
    "at the bottom of this file, so the Music web player keeps working."],
 "Subscription video on demand: global services":
   ["The paid streamers and their video CDNs. Only the video service is blocked, never the",
    "parent company: amazon.com, apple.com and google.com are all left alone."],
 "Subscription video on demand: India and South Asia":
   ["JioCinema and Disney+ Hotstar merged into JioHotstar in February 2025, so all three",
    "brand domains are listed."],
 "Live video, creator video and short video platforms":
   ["Live streaming, creator video and short video feeds. Vimeo is included because it is",
    "a video host; drop that one line if you need it for work."],
 "Blocked by explicit request: cloud storage and self hosted media":
   ["MEGA is general purpose cloud storage and Plex is a self hosted media server, so",
    "neither is piracy by itself. Both are here because you asked for them.",
    "plex.direct is the hostname Plex apps use to reach a server on your own LAN, so",
    "blocking it stops local playback too, not just plex.tv sign in. Drop that one line",
    "if you want your own server to keep working while the Plex service stays blocked."],
 "Torrent indexers and public trackers":
   ["Public and private torrent index sites. Mirror domains rotate constantly, so this",
    "section goes stale faster than the rest of the file."],
 "BitTorrent tracker endpoints":
   ["The announce hosts a torrent client talks to. Blocking these starves public torrents of",
    "peers even when the index site is reached some other way."],
 "Cloud torrent, debrid and seedbox services":
   ["Services that download or stream a torrent on their own servers so the user never runs",
    "a torrent client. webtor.io, Seedr, Real-Debrid, TorBox, Stremio and Usenet providers."],
 "Direct download hosts commonly paired with debrid services":
   ["File lockers that debrid services unlock. These do have legitimate uses, so delete this",
    "whole section if it gets in your way."],
 "Pirate streaming, unlicensed movie and TV sites":
   ["Unlicensed movie and TV streaming sites, including the Indian download portals."],
 "Anime and manga streaming":
   ["Unlicensed anime and manga readers. Licensed anime services are in the streaming",
    "sections above."],
 "Unlicensed live sports and IPTV":
   ["Illegal sports restreams and IPTV panels, plus a few licensed sports streamers."],
 "PC game piracy and repack sites":
   ["Repack and cracked game distributors, which are almost all torrent driven."],
}

def emit_sections(path, out):
    section = None
    buf = []
    for raw in open(path):
        line = raw.strip()
        if not line:
            continue
        if line.startswith('#SECTION '):
            if buf:
                out.extend(buf); out.append('')
            section = line[len('#SECTION '):]
            buf = ['!', '! ' + '-'*74, '! ' + section, '! ' + '-'*74]
            for n in NOTES.get(section, []):
                buf.append('! ' + n)
            buf.append('!')
            continue
        if line in KEEP:
            buf.append('||%s^' % line)
    if buf:
        out.extend(buf); out.append('')

out = []
for f in ('cur_youtube.txt', 'cur_streaming.txt', 'cur_extra_req.txt', 'cur_torrent.txt'):
    emit_sections(t(f), out)

# The extended block sourced from The Block List Project was removed in v1.2.0.
# DNS sweeping proved the domains resolve; it could not prove they are piracy
# sites. Spot checks found nasa.gov, worldwind.arc.nasa.gov, gutenberg.org,
# webcast.berkeley.edu, pbs.org and bittorrent.com in there, all legitimate sites
# that once ran a BitTorrent tracker for lawful distribution. 1148 domains that
# cannot be audited by hand are not worth six known false positives, so the whole
# block is gone. filter-compact.txt covers the same ground with regexes instead.
out += ['!', '! ' + '-'*74,
        '! Removed in v1.2.0: the extended block from The Block List Project',
        '! ' + '-'*74,
        '! That section carried 1148 upstream domains. Resolving them proved they are',
        '! alive, not that they are piracy sites. Auditing found nasa.gov, gutenberg.org,',
        '! pbs.org, webcast.berkeley.edu and bittorrent.com sitting in it, all legitimate',
        '! sites that once ran a BitTorrent tracker for lawful distribution. The rest',
        '! could not be checked by hand, so the whole block was dropped rather than',
        '! shipped on trust. See filter-compact.txt for regex based coverage instead.',
        '!']
out.append('')

body = '\n'.join(out)
full = open(t('header.txt')).read() + body + open(t('footer.txt')).read()
nb = full.count('\n||')
na = full.count('\n@@')
import re
full = re.sub(r'(?m)^! Total rules: .*$',
              '! Total rules: %d blocking rules, %d exception rules' % (nb, na), full)
open(os.path.join(ROOT, 'filter.txt'), 'w').write(full)
print('wrote filter.txt: %d blocking, %d exception' % (nb, na))
