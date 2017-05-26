#!/bin/sh

latest="pickles/`ls -1t pickles/ | head -1`"
python -u cancelot/oneshot.py $latest 2>&1 | tee -i -a logs/`date +%s`.log

latest="`ls -1t *pickle | head -1`"
mv $latest pickles/
ln -s pickles/$latest pickles/latest.pickle
rm *.pickle
