#!/bin/bash

for ((i=9;i<10;i++));
do 
    vidNum="coldwater-5-$i" yq -i '.default.video_name = env(vidNum)' configuration.yml
    python entrance.py
done
