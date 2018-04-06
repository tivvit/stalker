#!/usr/bin/env bash

export DISPLAY=':0.0'

PC="pc"

STALKER_DIR=$HOME/stalker/
if [ ! -d "$STALKER_DIR" ]; then
  mkdir -p $STALKER_DIR
fi

while true; do
  FILE=$STALKER_DIR`date +%y-%m-%d`.${PC}.log
  ERR_FILE=$HOME/stalker/`date +%y-%m-%d`.${PC}.err.log
  TITLE=`xdotool getactivewindow getwindowname 2>> $ERR_FILE`
  PROC=`ps -fp $(xdotool getactivewindow getwindowpid) -o cmd= 2>> $ERR_FILE`
  echo "{\"timestamp\": `date +%s.%N`, \"title\": \"$TITLE\", \"proc\":\"$PROC\"}" >> ${FILE}
  sleep 0.5
done
