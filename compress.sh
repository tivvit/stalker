#!/usr/bin/env bash
find ~/stalker/ -mtime +1 -print -exec gzip {} \;