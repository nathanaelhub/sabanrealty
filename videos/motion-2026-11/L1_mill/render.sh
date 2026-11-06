#!/bin/bash
# ./render.sh = full render to ../output/   ./render.sh --stills 1.5,6.2 = stills in ../build/L1_mill/stills/
exec "$(dirname "$0")/../shared/render.sh" L1_mill "$@"
