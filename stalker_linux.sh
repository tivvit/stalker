#!/usr/bin/env bash

export DISPLAY=':0.0'

while true; do
  FILE=$HOME/stalker/`date +%y-%m-%d`.log
  ERR_FILE=$HOME/stalker/`date +%y-%m-%d`.log
  TITLE=`xdotool getactivewindow getwindowname 2>> $ERR_FILE`
  PROC=`ps -fp $(xdotool getactivewindow getwindowpid) -o cmd= 2>> $ERR_FILE`
  echo "{\"timestamp\": `date +%s.%N`, \"title\": \"$TITLE\", \"proc\":\"$PROC\"}" >> $FILE
  sleep 0.5
done
