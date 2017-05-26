#!/bin/sh

python -u cancelot/oneshot.py pickles/`ls -1t pickles/ | head -1` 2>&1 | tee -i -a logs/`date +%s`.log
mv `ls -1t *pickle | head -1` pickles/
rm *.pickle
