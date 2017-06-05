#!/bin/sh

mkdir -p logs pickles

latest="pickles/`ls -1t pickles/ | head -1`"
python -u oneshot.py $latest 2>&1 | tee -i -a logs/`date +%s`.log

latest="`ls -1t *pickle | head -1`"
mv $latest pickles/
rm -f *.pickle

cd pickles
ln -sf $latest latest.pickle
