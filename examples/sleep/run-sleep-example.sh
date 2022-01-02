#!/bin/bash

python3 server/manage.py runserver &

pids=""

sleep 1

for i in `seq 0 3`; do
   python3 client/main.py --client_id=$i --cache_id=1 --schema_path=./examples/sleep/schema.yaml --repo_state_path=. &
   pids="$pids $!"
   sleep 1
done

wait $pids

ret_code=$?

pkill -f runserver

exit $ret_code
