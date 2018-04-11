#!/usr/bin/env bash
find ~/stalker/ -name "*.log" -mtime +0 -print -exec gzip {} \;