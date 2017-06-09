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

cc = bids.cancan(now + 24*60*60)

ccc = []
for bid in sorted(cc, key=lambda x: x.timeexpires):
    atstake = bid.deedsize * 0.005
    if bid.timeexpires < now + 24*60*60 and atstake >= web3.toWei(1, 'finney'): #and atstake < web3.toWei(1, 'finney'):
        #bid.display(web3)
        ccc.append(copy.copy(bid))
