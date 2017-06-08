#!/usr/bin/env python
# ENS "stale bid" pickle update script, one-shot.
# Author: Noel Maersk
# License: All rights reserved. Forbidden to distribute.

import sys

from web3 import Web3, IPCProvider

import cancelot

# DEBUG
pickleatblocknums = [
    3664565, # a little before first reveal event
    3666565  # ~ 800 blocks before first cancellation

]

# DEBUG: global for dropping to REPL on failure
web3 = Web3(IPCProvider())
bids = cancelot.BidStore(web3)

def main():
    # log/state filenames and loop limiting
    starttime = cancelot.utils.now()
    startblock = web3.eth.blockNumber

    # for processing historic blocks in batches
    blocknum = cancelot.utils.ENSLAUNCHBLOCK
    blockbatchsize = 100

    # override the latter two if pickle specified
    if len(sys.argv) == 2:
        (bidstore, blocknum) = cancelot.utils.load_pickled_bids(sys.argv[1])
        bids.store = bidstore

    while blocknum <= startblock:
        filt = web3.eth.filter({
            'fromBlock': blocknum,
            'toBlock': blocknum + blockbatchsize - 1, # magicnum -1: prevent overlap
            'address': cancelot.utils.REGISTRAR #,'topics': list(cancelot.handlers.keys())
        })
        events = filt.get(only_changes = False)
        web3.eth.uninstallFilter(filt.filter_id) # TODO: can filter be modified instead?

        bids.handle_events(events)

        # DEBUG save progress
        if blocknum in pickleatblocknums:
            cancelot.utils.pickle_bids(bids.store, starttime, blocknum)

        blocknum += blockbatchsize

    # having finished, save unconditionally
    cancelot.utils.pickle_bids(bids.store, starttime, blocknum)

    return # main()

if __name__ == '__main__':
    main()
