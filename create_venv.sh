#!/bin/bash

. env.sh

rm -rf $venv_dir


virtualenv --no-site-packages $venv_dir
. ${venv_dir}/bin/activate
pip install -r required_packages
