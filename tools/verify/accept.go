package main

import (
	"fmt"
	"os"
	"strings"

	"github.com/AdguardTeam/urlfilter"
	"github.com/AdguardTeam/urlfilter/filterlist"
)

func main() {
	data, _ := os.ReadFile(os.Args[1])
	lst := filterlist.NewString(&filterlist.StringConfig{ID: 1, RulesText: string(data), IgnoreCosmetic: true})
	rs, _ := filterlist.NewRuleStorage([]filterlist.Interface{lst})
	e := urlfilter.NewDNSEngine(rs)

	mustBlock := []string{
		"youtube.com", "www.youtube.com", "m.youtube.com", "youtube.de", "youtube.co.in", "youtu.be",
		"netflix.com", "primevideo.com", "hotstar.com", "jiohotstar.com", "disneyplus.com",
		"twitch.tv", "tiktok.com", "vimeo.com", "crunchyroll.com",
		"mega.nz", "plex.tv", "plex.direct",
		"thepiratebay.org", "www.thepiratebay.org", "1337x.to", "www.1337x.to", "1377x.to",
		"yts.rs", "eztv.re", "nyaa.si", "rutracker.org", "torrentgalaxy.mx",
		"webtor.io", "seedr.cc", "real-debrid.com", "torbox.app", "strem.io",
		"fmovies.to", "soap2day.to", "9anime.to", "streameast.to", "fitgirl-repacks.site",
		"tracker.opentrackr.org", "open.stealth.si",
		// native app endpoints
		"uts-api.itunes.apple.com", "play-edge.itunes.apple.com", "hls-svod.itunes.apple.com",
		"peacock.tv", "hses1.akamaized.net", "avodmp4s3ww-a.akamaihd.net",
		"api-global.netflix.com", "atv-ps.amazon.com", "api.hotstar.com",
		"disney.api.edge.bamgrid.com", "gql.twitch.tv", "apiv2.sonyliv.com",
	}
	mustAllow := []string{
		"music.youtube.com", "googlevideo.com", "youtubei.googleapis.com", "i.ytimg.com",
		"yt3.googleusercontent.com", "accounts.google.com",
		"spotify.com", "scdn.co", "encore.scdn.co", "spotifycdn.com",
		"music.apple.com", "itunes.apple.com", "mzstatic.com",
		"music.amazon.com", "music.amazon.in", "m.media-amazon.com",
		"soundcloud.com", "sndcdn.com", "deezer.com", "tidal.com", "jiosaavn.com",
		"gaana.com", "wynk.in", "bandcamp.com", "bcbits.com", "last.fm",
		"amazon.com", "apple.com", "google.com", "googleapis.com", "amazonaws.com",
		"archive.org", "torrent.ubuntu.com", "torrent.fedoraproject.org",
		"academictorrents.com", "linuxtracker.org", "bittorrent.com",
		"themoviedb.org", "api.themoviedb.org", "thetvdb.com", "musicbrainz.org",
		"trakt.tv", "imdb.com", "jellyfin.org", "github.com", "tracker.corp.internal",
		// must survive the app rules: shared CDN parents and Apple Music playback
		"akamaized.net", "e1234.akamaized.net", "akamaihd.net", "cdn.example.akamaihd.net",
		"audio-ssl.itunes.apple.com", "amp-api.music.apple.com", "aod-ssl.mzstatic.com",
		"a2z.com", "unagi.amazon.com", "amazon.com",
	}

	verdict := func(h string) (bool, string) {
		res, ok := e.Match(h)
		if !ok || res.NetworkRule == nil {
			return false, "no match"
		}
		if res.NetworkRule.Whitelist {
			return false, "allowed by " + res.NetworkRule.String()
		}
		return true, res.NetworkRule.String()
	}

	failB, failA := 0, 0
	fmt.Println("MUST BLOCK:")
	for _, h := range mustBlock {
		if b, r := verdict(h); !b {
			fmt.Printf("   FAIL %-32s %s\n", h, r)
			failB++
		}
	}
	if failB == 0 {
		fmt.Printf("   all %d blocked\n", len(mustBlock))
	}
	fmt.Println("MUST STAY REACHABLE:")
	for _, h := range mustAllow {
		if b, r := verdict(h); b {
			fmt.Printf("   FAIL %-32s BLOCKED by %s\n", h, r)
			failA++
		}
	}
	if failA == 0 {
		fmt.Printf("   all %d reachable\n", len(mustAllow))
	}
	fmt.Printf("\n%s: block-failures=%d allow-failures=%d\n",
		strings.TrimPrefix(os.Args[1], "/Users/aman.kumar/personal/video-dns-blocklist/"), failB, failA)
}
