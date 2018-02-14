#/bin/bash

. env.sh

ps aux | grep ${run_script} | awk -F ' ' '{print $2}' | xargs kill