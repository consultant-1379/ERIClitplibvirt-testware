#!/bin/sh
####################################
#
# System Memory.
#
####################################

free -m | awk 'NR==2{printf "Memory Usage: %s/%sMB (%.2f%%)\n", $3,$2,$3*100/$2 }' > /tmp/Memory_Usage.log
df -h | awk '$NF=="/"{printf "Disk Usage: %d/%dGB (%s)\n", $3,$2,$5}' > /tmp/Disk_Usage.log
top -bn1 | grep load | awk '{printf "CPU Load: %.2f\n", $(NF-2)}' > /tmp/CPU_Load.log
