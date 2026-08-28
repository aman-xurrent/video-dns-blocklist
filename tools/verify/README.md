# Verifiers

These run against AdGuard's own engine, `github.com/AdguardTeam/urlfilter`, not against
a regex library. That distinction caught two bugs that a plain regex test cannot see.

```sh
cd tools/verify
go mod init verify && go get github.com/AdguardTeam/urlfilter@latest

# acceptance: 40 hostnames that must be blocked, 46 that must stay reachable
go run accept.go ../../filter-compact.txt

# full sweep: coverage, guard list, collateral against a top-domains corpus
go run engine_test.go ../../filter-compact.txt must_block.txt guard.txt top20k.txt
```

## Two things a regex library will not tell you

**1. Regex rules do not match subdomains.** `||1337x.to^` covers `www.1337x.to`.
`/^1337x\./` does not. Every pattern in the compact list is written `(^|\.)` for this
reason. An early draft leaked 1469 of 2964 hostnames to this.

**2. Top level alternation silently half-works.** The engine indexes each rule by one
literal substring pulled out of the pattern, so only the first branch is ever reachable:

```
/1377x/         1377x.to -> blocked
/1337x|1377x/   1377x.to -> NOT BLOCKED
/1337x|1377x/   1337x.to -> blocked
```

So `a|b|c` at the top level must be split into three rules. `build_compact.py` does the
split automatically, but if you hand write a pattern, keep the alternation inside a
group that shares a literal with every branch: `/(^|\.)torrent(fu|[a-eg-z0-9-])/` is
fine because `torrent` is common to every match.
