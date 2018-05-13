#!/bin/bash

if [[ $# -lt 2 ]] ; then
    echo "Usage <virtual env path> <script to run path>"
    exit 0
fi

source $1/bin/activate
$2 "${@:3}"
rc=$?
deactivate

if [[ $? == 0 ]]; then
  exit $rc
fi

