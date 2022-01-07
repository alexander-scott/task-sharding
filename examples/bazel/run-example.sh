#!/bin/bash

python3 server/manage.py runserver &

sleep 1

python3 server/manage.py runworker controller &

sleep 1

python3 client/main.py --client_id=1 --cache_id=1 --schema_path=./examples/bazel/schema.yaml --repo_state_path=. --workspace_path=./examples/bazel

ret_code=$?

pkill -f runworker
pkill -f runserver

exit $ret_code
