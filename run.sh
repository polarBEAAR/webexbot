#/bin/bash

(/bin/bash /srv/webexbot.git/run_bot.sh &)

sleep 3

ps aux | grep webex | awk -F ' ' '{print $2}' > /tmp/bot.pid