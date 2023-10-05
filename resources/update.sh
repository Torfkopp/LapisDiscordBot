#!/bin/bash

echo "Time to update"
git pull origin master
sleep 20
echo "Restart Bot"
python3.11 main.py

$SHELL