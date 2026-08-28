"""Build filter-compact.txt: the same coverage as filter.txt, squeezed under the
1000 rule cap on the AdGuard DNS Personal plan by swapping ~1642 literal domain
rules for a small set of RE2 regular expressions.

Run from the repo root:  python3 tools/build_compact.py
"""
import os, re, datetime

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
def t(n): return os.path.join(HERE, n)

def lines(p):
    return [l.strip() for l in open(p) if l.strip() and not l.startswith('#')]

keep     = sorted(set(lines(t('compact_keep_literal.txt'))))
regexes  = lines(t('compact_regexes.txt'))
leftover = sorted(set(lines(t('compact_leftover.txt')))) if os.path.exists(t('compact_leftover.txt')) else []
allows   = [l.rstrip() for l in open(t('footer.txt')) if l.startswith('@@')]

SECTIONS = [
 ("Regular expression rules: the compressed half of the list",
  ["One regex replaces anywhere from three to several hundred literal domain rules.",
   "These cover YouTube country domains, torrent index brands and their rotating",
   "mirrors, tracker announce hosts, pirate streaming, anime, sports restreams and",
   "game repack sites. Because they match on brand rather than on an exact domain,",
   "they also catch next month's mirror, which the literal list could not.",
   "",
   "Syntax is /pattern/. AdGuard runs Go's regexp package, which is RE2, so there",
   "are no lookaheads or backreferences anywhere in here on purpose.",
   "Matching is unanchored against the full hostname, which is why almost every",
   "pattern below carries an explicit ^ or $."],
  [r if r.startswith(('@@','/')) else '/%s/' % r for r in regexes]),
 ("Literal rules: services that do not compress safely",
  ["Licensed streaming services, their video CDNs, cloud torrent and debrid",
   "providers, file lockers, MEGA and Plex. These are one-off brands with no shared",
   "pattern, so a regex would either miss them or overreach."],
  ['||%s^' % d for d in keep]),
]
if leftover:
    SECTIONS.append(("Literal rules: leftovers the regex pass could not fold in safely",
      ["Each of these resisted compression without risking a false positive, so it",
       "stayed a literal rule. Correctness beats a lower rule count."],
      ['||%s^' % d for d in leftover]))

def banner(title, notes):
    out = ['!', '! ' + '-'*74, '! ' + title, '! ' + '-'*74]
    for n in notes:
        out.append('! ' + n if n else '!')
    out.append('!')
    return out

body = []
for title, notes, rules in SECTIONS:
    body += banner(title, notes) + rules + ['']

full = open(t('compact_header.txt')).read() + '\n'.join(body) + open(t('footer.txt')).read()

n_re    = sum(1 for l in body if l.startswith('/') or l.startswith('@@/'))
n_lit   = sum(1 for l in body if l.startswith('||'))
n_allow = len(allows) + sum(1 for l in body if l.startswith('@@/'))
n_re    = sum(1 for l in body if l.startswith('/'))
total   = n_re + n_lit + n_allow

full = re.sub(r'(?m)^! Total rules: .*$',
    '! Total rules: %d (%d regex, %d literal block, %d exception). Cap is 1000.'
    % (total, n_re, n_lit, n_allow), full)
full = re.sub(r'(?m)^! Last modified: .*$',
    '! Last modified: ' + datetime.datetime.now(datetime.timezone.utc)
        .strftime('%Y-%m-%dT%H:%M:%S.000Z'), full)

open(os.path.join(ROOT, 'filter-compact.txt'), 'w').write(full)
print('filter-compact.txt: %d regex + %d literal + %d exception = %d rules (cap 1000)'
      % (n_re, n_lit, n_allow, total))
if total > 1000:
    raise SystemExit('OVER CAP by %d rules' % (total - 1000))
