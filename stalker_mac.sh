#!/usr/bin/env bash

PC="ntb"
while true; do
  FILE=$HOME/stalker/`date +%y-%m-%d`.${PC}.log
  ERR_FILE=$HOME/stalker/`date +%y-%m-%d`.${PC}.err.log
  /Users/vit.listik/git/stalker/active-win >> ${FILE} 2> ${ERR_FILE}
  sleep 0.5
done
