#!/usr/bin/env bash
set -e
PATH=$PATH:/usr/local/bin
PC="$1"
# backup
rclone copy ~/stalker g:stalker --exclude "`date +%y-%m-%d`.*"
# backup active (from this machine)
mkdir -p /tmp/stalker
cp ~/stalker/`date +%y-%m-%d`.${PC}.* /tmp/stalker
rclone copy /tmp/stalker g:stalker
rm /tmp/stalker/*
# download other machines
rclone copy g:stalker ~/stalker --exclude "`date +%y-%m-%d`.${PC}.*"
# delete non-compressed files on remote
for i in ~/stalker/*.log; do
    # exclude today
    if [[ $i != *"`date +%y-%m-%d`"* ]]; then
        # test gzip existence
        if [ -f "$i.gz" ]; then
            rm "$i"
            filename=$(basename -- "$i")
            rclone delete g:stalker/"$filename"
        fi
    fi
done