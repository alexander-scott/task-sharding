#!/bin/bash

python3 client/client.py 1 &
sleep 1
python3 client/client.py 2 &
wait
