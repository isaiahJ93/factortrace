#!/bin/bash

# This will help us see what needs to be changed
echo "Current button structure:"
grep -A15 "flex gap-3" src/app/page.tsx | head -20

echo -e "\nTo fix this manually:"
echo "1. In src/app/page.tsx, find the button group with 'flex gap-3'"
echo "2. Change the white button (Generate Report) to say 'View Reports' and onClick={() => router.push('/reports')}"
echo "3. The green button should already say 'Generate Report' and go to /emissions/new"
echo "4. Make sure the green button (Generate Report) comes first"
