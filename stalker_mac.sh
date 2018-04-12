#!/usr/bin/env bash

PC="ntb"

STALKER_DIR=$HOME/stalker/
if [ ! -d "$STALKER_DIR" ]; then
  mkdir -p $STALKER_DIR
fi

while true; do
  FILE=${STALKER_DIR}`date +%y-%m-%d`.${PC}.log
  ERR_FILE=${STALKER_DIR}`date +%y-%m-%d`.${PC}.err.log
  IDLETIME=`ioreg -c IOHIDSystem | awk '/HIDIdleTime/ {print int($NF/1000000)}'`
  /Users/vit.listik/git/stalker/active-win | /usr/local/bin/jq '. + {"idletime": '"${IDLETIME}"'}' -c >> ${FILE} 2> ${ERR_FILE}
  sleep 0.5
done
