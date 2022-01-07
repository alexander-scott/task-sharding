#!/bin/bash

python3 server/manage.py runserver &

sleep 1

python3 server/manage.py runworker controller &

sleep 1

cd examples/bazel

python3 -m venv venv/
source venv/bin/activate

pip3 install -r ../../server/requirements.txt
pip3 install ../../client/dist/task_sharding_client_alexander_scott-0.0.1-py3-none-any.whl

python3 main.py --client_id=1 --cache_id=1 --schema_path=schema.yaml --repo_state_path=. --workspace_path=.

ret_code=$?

deactivate
rm -rf venv

pkill -f runworker
pkill -f runserver

exit $ret_code
