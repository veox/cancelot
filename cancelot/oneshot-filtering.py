#!/usr/bin/env python
# ENS "stale bid" pickle update script, one-shot.
# Author: Noel Maersk
# License: All rights reserved. Forbidden to distribute.

import sys

from web3 import Web3, IPCProvider

import cancelot

def main():
    web3 = Web3(IPCProvider())

    # log/state filenames and loop limiting
    starttime = cancelot.now()
    startblock = web3.eth.blockNumber

    # 'msg.sender' + 'sealedBid -> BidInfo
    bids = {}
    # for processing historic blocks in batches
    blocknum = cancelot.enslaunchblock
    blockbatchsize = 1000

    # override the latter two if pickle specified
    if len(sys.argv) == 2:
        (bids, blocknum) = cancelot.load_pickled_bids(sys.argv[1])

    while blocknum <= startblock:
        filt = web3.eth.filter({
            'fromBlock': blocknum,
            'toBlock': blocknum + blockbatchsize,
            'address': cancelot.registrar #,'topics': list(cancelot.handlers.keys())
        })
        events = filt.get(only_changes = False)
        web3.eth.uninstallFilter(filt.filter_id) # TODO: can filter be modified instead?

        for ev in events:
            cancelot.check_event_log(ev, bids)

        blocknum += blockbatchsize

    # having finished, save unconditionally
    cancelot.pickle_bids(bids, starttime, blocknum)

    return # main()

if __name__ == '__main__':
    main()
