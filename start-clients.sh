#!/bin/bash

python3 client/main.py --client_id=1 --schema_path=./examples/sleep/schema.yaml &
sleep 1
python3 client/main.py --client_id=2 --schema_path=./examples/sleep/schema.yaml &
wait
