#!/usr/bin/env bash

while true; do
  FILE=$HOME/stalker/`date +%y-%m-%d`.log
  touch $FILE
  TITLE=`xdotool getactivewindow getwindowname`
  PROC=`ps -fp $(xdotool getactivewindow getwindowpid) -o cmd=`
  echo "{\"timestamp\": `date +%s.%N`, \"title\": \"$TITLE\", \"proc\":\"$PROC\"}" >> $FILE
  sleep 0.5
done
