#!/bin/bash

for data in 'contributions' 'votes'; do
    pushd "./data/$data"
    ./get_data.sh
    popd
done
