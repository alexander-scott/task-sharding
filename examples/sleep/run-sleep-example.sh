#!/bin/bash

python3 server/manage.py runserver &

sleep 1

python3 server/manage.py runworker controller &

sleep 1

pids=""
for i in `seq 0 2`; do
   python3 client/main.py --client_id=$i --cache_id=1 --schema_path=./examples/sleep/schema.yaml --repo_state_path=. &
   pids="$pids $!"
   sleep 1
done

wait $pids

ret_code=$?

pkill -f runworker
pkill -f runserver

exit $ret_code
