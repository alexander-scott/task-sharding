#!/bin/bash

python3 client/client.py client1 &
python3 client/client.py client2 &
wait
