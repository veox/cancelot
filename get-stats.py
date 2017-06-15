#!/usr/bin/env python
# Swipe through history to get stats. Based on oneshot.py
# Author: Noel Maersk
# License: GPLv3. See LICENSE.txt

import sys

from web3 import Web3, IPCProvider

import cancelot

# DEBUG: global for dropping to REPL on failure
web3 = Web3(IPCProvider())
bids = cancelot.BidStore(web3)

def numrange(fromnum, size):
    # magicnum -1: don't include range end
    return (fromnum, fromnum + size - 1)

def cb_handled():
    '''Callback to track handled events.'''
    pass

def main():
    # log/state filenames and loop limiting
    starttime = cancelot.utils.now()
    startblocknum = web3.eth.blockNumber

    # for processing historic blocks in batches
    batchsize = 100
    nbatches = 0

    # default from-block
    blocknum = cancelot.utils.ENSLAUNCHBLOCK
    # override if pickle specified
    if len(sys.argv) == 2:
        (bidstore, blocknum) = cancelot.utils.load_pickled_bids(sys.argv[1])
        bids.store = bidstore
    # calc to-block based on that
    (_, toblocknum) = numrange(blocknum, batchsize)

    while toblocknum <= startblocknum:
        filt = web3.eth.filter({
            'fromBlock': blocknum,
            'toBlock': toblocknum,
            'address': cancelot.utils.REGISTRAR #,'topics': list(cancelot.handlers.keys())
        })
        events = filt.get(only_changes = False)
        web3.eth.uninstallFilter(filt.filter_id) # TODO: can filter be modified instead?

        bids.handle_events(events, callback = cb_handled)

        # DEBUG save progress
        nbatches += 1
        if nbatches % batchsize == 0:
            cancelot.utils.pickle_bids(bids.store, starttime, toblocknum)

        (blocknum, toblocknum) = numrange(toblocknum+1, batchsize)

    # having finished, save unconditionally
    cancelot.utils.pickle_bids(bids.store, starttime, toblocknum)

    print('Finished! Processed', nbatches * batchsize, 'blocks.')

    return # main()

if __name__ == '__main__':
    main()
