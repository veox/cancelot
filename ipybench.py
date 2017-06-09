#!/usr/bin/env python
# WIP ipython bench generic imports and setup

import copy
import pprint
import random
import time

import cancelot

from web3 import Web3, IPCProvider
web3 = Web3(IPCProvider())

bids = cancelot.BidStore(web3)
(bidstore, blocknum) = cancelot.utils.load_pickled_bids('pickles/latest.pickle')
bids.store = bidstore

now = cancelot.utils.now()
