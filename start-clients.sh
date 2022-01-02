#!/bin/bash

python3 client/main.py --client_id=1 --cache_id=1 --schema_path=./examples/sleep/schema.yaml --repo_state_path=. &
sleep 1
python3 client/main.py --client_id=2 --cache_id=1 --schema_path=./examples/sleep/schema.yaml --repo_state_path=. &
wait
