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

extra = sorted(set(open(t('upstream_extra.txt')).read().split()))
out += ['!', '! ' + '-'*74,
        '! Extended coverage: torrent and piracy domains from The Block List Project',
        '! ' + '-'*74,
        '! Source: https://github.com/blocklistproject/Lists (piracy.txt and torrent.txt),',
        '! released into the public domain under the Unlicense.',
        '! Their raw lists carry a lot of dead weight, so every domain below was resolved on',
        '! 2026-08-28 and anything that came back NXDOMAIN or landed on a known domain-parking',
        '! IP was thrown away. Linux distro torrents (torrent.ubuntu.com, Fedora), archive.org',
        '! and tech news sites were removed by hand. Delete this whole block if you only want',
        '! the curated sections above.',
        '!']
out += ['||%s^' % d for d in extra]
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
