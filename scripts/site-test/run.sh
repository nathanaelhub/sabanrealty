#!/bin/bash
# Saban Realty site test runner.
#   bash scripts/site-test/run.sh          # local: static checks + browser tests
#   bash scripts/site-test/run.sh static   # local: static checks only (fast)
#   bash scripts/site-test/run.sh prod     # production: deploy + live spot checks
set -u
cd "$(dirname "$0")/../.."   # repo root
MODE="${1:-all}"

if [ "$MODE" = "prod" ]; then
  exec bash scripts/site-test/prod-check.sh
fi

echo "== Static checks =="
python3 scripts/site-test/checks.py
STATIC=$?

BROWSER=0
if [ "$MODE" != "static" ]; then
  echo
  echo "== Browser tests =="
  python3 -m http.server 8899 >/dev/null 2>&1 &
  SRV=$!
  sleep 1
  node scripts/site-test/browser-test.mjs
  BROWSER=$?
  kill $SRV 2>/dev/null
fi

echo
[ $STATIC -eq 0 ] && [ $BROWSER -eq 0 ] && { echo "SITE-TEST: ALL PASS"; exit 0; }
echo "SITE-TEST: FAILURES (static=$STATIC browser=$BROWSER)"
exit 1
