#!/bin/sh
## set consumer env variables
while read l; do
    [ -z "$l" ] && continue
    if ! echo $l | grep -q "###"; then
        export $l;
    fi
done < .env
python -u main.py