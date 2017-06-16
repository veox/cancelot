#!/usr/bin/env python
# Swipe through history to get stats. Based on oneshot.py.
# Requires a "full sync" since .eth Regitrar's launch date to
# guarantee correctness when looking up historic Deed balance.
# Author: Noel Maersk
# License: GPLv3. See LICENSE.txt

import pprint
import sys

from web3 import Web3, IPCProvider

import cancelot

# DEBUG: global for dropping to REPL on failure
web3 = Web3(IPCProvider())
bids = cancelot.BidStore(web3)

def numrange(fromnum, size):
    # magicnum -1: don't include range end
    return (fromnum, fromnum + size - 1)

# counters
nbids = {'placed': 0, 'active': 0, 'revealed': 0, 'cancelled': 0}
# eth amount tracking
wei =   {'placed': 0, 'active': 0, 'revealed': 0, 'cancelled': 0}

def cb_handled(bid, event, eventtype, handler):
    '''Callback to track handled events.'''

    if eventtype == cancelot.EventType.PLACED:
        nbids['active'] += 1
        nbids['placed'] += 1

        # work around scroogey BidStore - do actually get deed size
        #bid.update(web3, atblock = event['blockNumber'])

        # HACK: get deed size from submitting transaction (unreliable)
        tx = web3.eth.getTransaction(event['transactionHash'])
        # assume the whole value is for one bid
        bid.deedsize = tx['value']
        # convenience
        key = (bid.bidder, bid.seal)
        # HACK: update store for later ref
        bids.set(key, bid)

        wei['active'] += bid.deedsize
        wei['placed'] += bid.deedsize
    elif eventtype == cancelot.EventType.REVEALED:
        nbids['active'] -= 1
        nbids['revealed'] += 1

        # `bid` should have pre-reveal deedsize
        assert(bid.deedsize != 0)

        # HACK: get deed size from reveal data (should be reliable)
        tx = web3.eth.getTransaction(event['transactionHash'])
        OFFSET = 2+8+64 # 2 for '0x', 8 for function signature, 64 for bytes(32).hex() value
        bidsize = web3.toDecimal('0x' + tx['input'][OFFSET:OFFSET+64])

        wei['active'] -= bid.deedsize
        wei['revealed'] += bidsize
    elif eventtype == cancelot.EventType.CANCELLED:
        nbids['active'] -= 1
        nbids['cancelled'] += 1

        # `bid` should have pre-cancel deedsize
        assert(bid.deedsize != 0)

        wei['active'] -= bid.deedsize
        wei['cancelled'] += bid.deedsize

    return

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

        bids.handle_events(events, cb = cb_handled)

        # DEBUG save progress
        nbatches += 1
        if nbatches % batchsize == 0:
            cancelot.utils.pickle_bids(bids.store, starttime, toblocknum)

        (blocknum, toblocknum) = numrange(toblocknum+1, batchsize)

    # having finished, save unconditionally
    cancelot.utils.pickle_bids(bids.store, starttime, toblocknum)

    print('Finished! Processed', nbatches * batchsize, 'blocks.')

    # TODO: proper out
    pprint.pprint(nbids)
    pprint.pprint(wei)

    return # main()

if __name__ == '__main__':
    main()
