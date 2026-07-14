#!/bin/bash
# Post-push production verification for sabanrealty.com.
#   bash scripts/site-test/prod-check.sh
# Waits for the GitHub Pages build of the current HEAD, then spot-checks live URLs.
set -u
cd "$(dirname "$0")/../.."
FAIL=0
chk() { # name, condition(0=ok)
  if [ "$2" -eq 0 ]; then echo "  PASS: $1"; else echo "  FAIL: $1"; FAIL=1; fi
}

HEAD=$(git rev-parse HEAD | cut -c1-8)
echo "== Waiting for GitHub Pages build of $HEAD (max ~4 min) =="
BUILT=1
for i in $(seq 1 24); do
  ST=$(gh api repos/nathanaelhub/sabanrealty/pages/builds/latest 2>/dev/null \
       | python3 -c "import sys,json;d=json.load(sys.stdin);print(d.get('status'),d.get('commit','')[:8],(d.get('error') or {}).get('message'))" 2>/dev/null)
  echo "  t+$((i*10))s: $ST"
  echo "$ST" | grep -q "built $HEAD" && { BUILT=0; break; }
  echo "$ST" | grep -qi "errored" && break
  sleep 10
done
chk "Pages build completed for HEAD ($HEAD)" $BUILT

echo "== Live spot checks =="
for u in "" "buy/" "rent/" "blog/" "sitemap.xml"; do
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "https://sabanrealty.com/$u")
  [ "$CODE" = "200" ]; chk "https://sabanrealty.com/$u -> 200 (got $CODE)" $?
done

# one listing + one blog post straight from the local sitemap
LISTING=$(grep -oE '<loc>https://sabanrealty\.com/properties/[a-z0-9-]+/</loc>' sitemap.xml | head -1 | sed 's/<[^>]*>//g')
POST=$(grep -oE '<loc>https://sabanrealty\.com/blog/[a-z0-9-]+/</loc>' sitemap.xml | head -1 | sed 's/<[^>]*>//g')
for u in "$LISTING" "$POST"; do
  [ -n "$u" ] || continue
  CODE=$(curl -s -o /dev/null -w '%{http_code}' "$u")
  [ "$CODE" = "200" ]; chk "$u -> 200 (got $CODE)" $?
done

# assets + invariants
curl -s https://sabanrealty.com/css/styles.min.css | grep -q 'property-ribbon'; chk "min CSS live (has property-ribbon)" $?
CODE=$(curl -s -o /dev/null -w '%{http_code}' https://sabanrealty.com/js/main.min.js)
[ "$CODE" = "200" ]; chk "main.min.js serves (got $CODE)" $?
N=$(curl -s "$LISTING" | grep -c 'content="noindex"'); [ "$N" = "0" ]; chk "listing pages indexable (noindex=$N)" $?
N=$(curl -s https://sabanrealty.com/property-detail.html | grep -c 'content="noindex"'); [ "$N" = "1" ]; chk "bare engine is noindex" $?

echo
[ $FAIL -eq 0 ] && { echo "PROD-CHECK: ALL PASS"; exit 0; }
echo "PROD-CHECK: FAILURES"
exit 1
