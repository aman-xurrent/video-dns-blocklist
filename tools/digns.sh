#!/bin/zsh
d="$1"
# strip to registrable-ish zone check: ask for NS on the name itself
ns=$(dig +short +time=3 +tries=2 NS "$d" @1.1.1.1 2>/dev/null | head -1)
st=$(dig +time=3 +tries=2 A "$d" @1.1.1.1 2>/dev/null | grep -oE 'status: [A-Z]+' | head -1 | awk '{print $2}')
w=$(dig +short +time=3 +tries=2 A "www.$d" @1.1.1.1 2>/dev/null | grep -cE '^[0-9]+\.')
echo "$d|ns=${ns:-none}|status=${st:-none}|www=${w}"
