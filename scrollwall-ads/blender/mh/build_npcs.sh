#!/bin/bash
# Subway commuters for Reel 2 (MakeHuman CC0 assets), PS1-baked like the hero.
# Usage: bash build_npcs.sh [name ...]   -> /home/user/mh/npc/<name>_npc.blend
cd "$(dirname "$0")"
PY=/home/user/blendenv/bin/python
OUT=/home/user/mh/npc
mkdir -p $OUT
build() {  # name proxy macro race skin hair clothes keys
  local n=$1
  PROXY=$2 MACRO=$3 RACE=$4 SKIN=$5 HAIRSTYLE=$6 CLOTHES=$7 $PY build_scroller.py $OUT/$n.blend > $OUT/$n.log 2>&1 &&
  local D=$OUT
  IN=$D/$n.blend OUT=$D/${n}_npc.blend IMG=$D/${n}_npcskin.png PROXY=$2 CLOTH_KEYS=$8 HAIRSTYLE=$6 HAIR=0.35 EXTRUDE=0.12 RAYDIST=0.3 \
    $PY cloth_bake.py >> $OUT/$n.log 2>&1 && echo "built $n" || echo "FAILED $n (see $OUT/$n.log)"
}
want() { [ -z "$ARGS" ] || [[ " $ARGS " == *" $1 "* ]]; }
ARGS="$*"
want office   && build office   female1605 '{"gender":0,"age":0.55,"weight":0.45,"height":0.5}' '{"caucasian":0.7,"asian":0.3}' young_caucasian_female bob02 female_casualsuit01,shoes02 casualsuit,shoes
want worker   && build worker   proxy741 '{"gender":1,"age":0.85,"weight":0.65,"muscle":0.5}' '{"african":1}' old_african_male short04 male_worksuit01,shoes03 worksuit,shoes
want student  && build student  female1605 '{"gender":0,"age":0.47,"weight":0.42,"height":0.55}' '{"asian":1}' young_asian_female ponytail01 female_casualsuit02,shoes04 casualsuit,shoes
want business && build business proxy741 '{"gender":1,"age":0.6,"weight":0.55}' '{"caucasian":1}' middleage_caucasian_male short01 male_elegantsuit01,shoes05 elegantsuit,shoes
