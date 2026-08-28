#!/bin/zsh
d="$1"
out=$(dig +short +time=2 +tries=1 A "$d" @1.1.1.1 2>/dev/null | grep -E '^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$' | head -1)
if [ -n "$out" ]; then echo "$d"; fi
