#!/bin/bash
# ./render.sh = full render to ../output/   ./render.sh --stills 1.5,6.2 = stills in ../build/V1_catseye/stills/
exec "$(dirname "$0")/../shared/render.sh" V1_catseye "$@"
