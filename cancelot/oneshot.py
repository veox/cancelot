#!/usr/bin/env python
# ENS "stale bid" pickle update script, one-shot.
# Author: Noel Maersk
# License: All rights reserved. Forbidden to distribute.

import sys
import time

from web3 import Web3, IPCProvider

import cancelot

def main():
    web3 = Web3(IPCProvider())

    # log/state filenames and loop limiting
    starttime = int(time.time())
    startblock = web3.eth.blockNumber
    # "start" one block behind, to capture the `enslaunchblock` with increment-first loop
    blocknum = cancelot.enslaunchblock - 1

    # 'msg.sender' + 'sealedBid -> BidInfo
    bids = {}

    # use existing pickle if provided
    if len(sys.argv) == 2:
        (bids, blocknum) = cancelot.load_pickled_bids(sys.argv[1])

    # loop until blocknum == startblock
    while blocknum < startblock:
        blocknum += 1
        txcount = web3.eth.getBlockTransactionCount(blocknum)
        if txcount == 0: continue # short-circuit

        # iterate over transactions
        for txi in range(txcount):
            tx = web3.eth.getTransactionFromBlock(blocknum, hex(txi)) # hex(txi) - bug?..
            if tx['to'] == cancelot.registrar:
                cancelot.check_tx(tx, bids)

        # write to file once in a while (full run takes an hour or more...)
        if int(blocknum)%10000 == 0:
            cancelot.pickle_bids(bids, starttime, blocknum)
    # having finished, save unconditionally
    cancelot.pickle_bids(bids, starttime, blocknum)

    return # main()

if __name__ == '__main__':
    main()
