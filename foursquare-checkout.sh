#!/bin/bash

me="$(dirname $(readlink -nf $0))"
user_id=7365680
ics=52WA2WM1E0BM3C5TUCOJOXTHOAW2NHVQ.ics
#ics=52WA2WM1E0BM3C5TUCOJOXTHOAW2NHVQ-new.ics
#date_from=2021-01-01
remote=meku@meku.org:public_html/4sq-checkout/

set -e

cd $me
source venv/bin/activate
./foursquare-api.py checkins $user_id
./ics_export.py $user_id $ics
scp -C $ics $remote
