#/bin/bash

. env.sh

. ${vname}/bin/activate
cd $directory
python ${run_script}
