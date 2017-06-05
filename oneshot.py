#!/usr/bin/env python
# ENS "stale bid" pickle update script, one-shot.
# Author: Noel Maersk
# License: All rights reserved. Forbidden to distribute.

import sys

from web3 import Web3, IPCProvider

import cancelot

# DEBUG
pickleatblocknums = [3664565]

def main():
    web3 = Web3(IPCProvider())

    # log/state filenames and loop limiting
    starttime = cancelot.utils.now()
    startblock = web3.eth.blockNumber

    # 'msg.sender' + 'sealedBid -> BidInfo
    bids = cancelot.BidStore(web3)
    # for processing historic blocks in batches
    blocknum = cancelot.utils.ENSLAUNCHBLOCK
    blockbatchsize = 100

    # override the latter two if pickle specified
    if len(sys.argv) == 2:
        (bidstore, blocknum) = cancelot.load_pickled_bids(sys.argv[1])
        bids.store = bidstore

    while blocknum <= startblock:
        filt = web3.eth.filter({
            'fromBlock': blocknum,
            'toBlock': blocknum + blockbatchsize,
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
