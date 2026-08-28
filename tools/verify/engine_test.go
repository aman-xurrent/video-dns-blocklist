package main

import (
	"bufio"
	"fmt"
	"os"
	"strings"

	"github.com/AdguardTeam/urlfilter"
	"github.com/AdguardTeam/urlfilter/filterlist"
)

func lines(p string) []string {
	f, _ := os.Open(p)
	defer f.Close()
	var out []string
	s := bufio.NewScanner(f)
	s.Buffer(make([]byte, 4*1024*1024), 4*1024*1024)
	for s.Scan() {
		t := strings.TrimSpace(s.Text())
		if t != "" && !strings.HasPrefix(t, "#") {
			out = append(out, t)
		}
	}
	return out
}

func main() {
	filterPath, coverPath, guardPath, topPath := os.Args[1], os.Args[2], os.Args[3], os.Args[4]
	data, err := os.ReadFile(filterPath)
	if err != nil {
		panic(err)
	}
	lst := filterlist.NewString(&filterlist.StringConfig{ID: 1, RulesText: string(data), IgnoreCosmetic: true})
	rs, err := filterlist.NewRuleStorage([]filterlist.Interface{lst})
	if err != nil {
		panic(err)
	}
	e := urlfilter.NewDNSEngine(rs)
	fmt.Printf("### %s\n", filterPath)
	fmt.Printf("engine loaded %d rules\n", e.RulesCount)

	blocked := func(h string) (bool, string) {
		res, ok := e.Match(h)
		if !ok || res.NetworkRule == nil {
			return false, ""
		}
		if res.NetworkRule.Whitelist {
			return false, "allowed by " + res.NetworkRule.String()
		}
		return true, res.NetworkRule.String()
	}

	var miss []string
	cov := lines(coverPath)
	for _, h := range cov {
		if b, _ := blocked(h); !b {
			miss = append(miss, h)
		}
	}
	fmt.Printf("COVERAGE : %d/%d blocked, %d LEAKED\n", len(cov)-len(miss), len(cov), len(miss))
	for i, m := range miss {
		if i < 25 {
			fmt.Println("   LEAK:", m)
		}
	}
	if len(miss) > 25 {
		fmt.Printf("   ... and %d more\n", len(miss)-25)
	}

	var gh []string
	for _, h := range lines(guardPath) {
		if b, r := blocked(h); b {
			gh = append(gh, fmt.Sprintf("%s  by %s", h, r))
		}
	}
	fmt.Printf("GUARD    : %d hits (must be 0)\n", len(gh))
	for _, g := range gh {
		fmt.Println("   HIT:", g)
	}

	intended := map[string]bool{}
	intendedSrc := cov
	if len(os.Args) > 5 {
		intendedSrc = lines(os.Args[5])
	}
	for _, d := range intendedSrc {
		intended[d] = true
	}
	isSub := func(h string) bool {
		parts := strings.Split(h, ".")
		for i := 0; i < len(parts)-1; i++ {
			if intended[strings.Join(parts[i:], ".")] {
				return true
			}
		}
		return intended[h]
	}
	var col []string
	for _, h := range lines(topPath) {
		if b, r := blocked(h); b && !isSub(h) {
			col = append(col, fmt.Sprintf("%-42s <- %s", h, r))
		}
	}
	fmt.Printf("TOP20K   : %d unintended blocks\n", len(col))
	for i, c := range col {
		if i < 45 {
			fmt.Println("   ", c)
		}
	}
	if len(col) > 45 {
		fmt.Printf("    ... and %d more\n", len(col)-45)
	}
	fmt.Printf("RESULT leaks=%d guardhits=%d collateral=%d\n\n", len(miss), len(gh), len(col))
}
