#!/bin/bash

python3 server/manage.py runserver &
python3 server/manage.py runworker controller &

sleep 1

cd examples/sleep

python3 -m venv venv/
source venv/bin/activate

pip3 install -r ../../server/requirements.txt
pip3 install ../../client/dist/task_sharding_client_alexander_scott-0.0.1-py3-none-any.whl

pids=""
for i in `seq 0 2`; do
   python3 main.py --client_id=$i --cache_id=1 --schema_path=schema.yaml &
   pids="$pids $!"
   sleep 1
done

wait $pids

ret_code=$?

deactivate
rm -rf venv

pkill -f runworker
pkill -f runserver

exit $ret_code
