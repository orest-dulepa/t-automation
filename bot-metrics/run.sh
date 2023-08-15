#!/bin/bash

GIT_PATH=${1:-git@bitbucket.org}
bots=( "be1-initial-invoicing" "be2-invoice-followup" "be3-primary-claims" "logs1-new-case-entry" "logs2-missing-document" "roig1-data-cleanse" "rsma1-bk-close-case-bot" "rsma1-bk-e-filing-bot" "rsma1-bk-nopc-new-case-entry" "tbh1-rosey" "tbh2-vision" "tbh3-r2-d2" "tbh4-bumblebee" "tbh5-kitt" )

for i in "${bots[@]}"
do
  echo Stats for: $i
  git clone -q $GIT_PATH:ta/$i.git
  python3 bot_stats_combined.py $i
  rm -rf $i
  echo
  echo
done

