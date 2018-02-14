#/bin/bash

(/bin/bash /srv/webexbot/run_bot.sh &)

sleep 3

ps aux | grep webex5 | awk -F ' ' '{print $2}' > /tmp/bot.pid