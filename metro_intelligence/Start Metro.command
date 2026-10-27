#!/bin/bash
cd -- "$(dirname -- "$0")" || exit 1
python3.12 launch_local.py
result=$?
if [ "$result" -ne 0 ]; then
 read -r -p 'Install Python 3.12 from python.org, then try again. Press Enter to close.'
fi
exit "$result"
