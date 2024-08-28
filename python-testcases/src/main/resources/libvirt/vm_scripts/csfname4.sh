#!/bin/bash
crontab -l > /tmp/mycron
#echo new cron into cron file
echo "* * * * * date 2>&1 >> /tmp/timestampfile.txt" >> /tmp/mycron
#install new cron file
crontab /tmp/mycron
rm -rf /tmp/mycron
