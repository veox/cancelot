#!/usr/bin/env python
# ENS "stale bid" cancellation opportunity monitor. One-shot. Pickle hoarder.
# Author: Noel Maersk
# License: All rights reserved. Forbidden to distribute.

import pickle
import pprint
import sys
import time

import decimal

from web3 import Web3, IPCProvider
web3 = Web3(IPCProvider()) # TODO: don't use global


def main():
    # log/state filenames and loop limiting
    starttime = int(time.time())
    startblock = web3.eth.blockNumber
    # "start" one block behind, to capture the `enslaunchblock` with increment-first loop
    blocknum = enslaunchblock - 1

    # msg.sender+sealedBid -> bid info
    bids = {}

    # use existing pickle if provided
    if len(sys.argv) == 2:
        bids, blocknum = load_pickled_bids(sys.argv[1])

    # loop until blocknum == startblock
    while blocknum < startblock:
        blocknum += 1
        txcount = web3.eth.getBlockTransactionCount(blocknum)
        if txcount == 0: continue # short-circuit

        # iterate over transactions
        for txi in range(txcount):
            tx = web3.eth.getTransactionFromBlock(blocknum, hex(txi))
            if tx['to'] == registrar:
                check_tx(tx, bids)

        # write to file once in a while (full run takes an hour or more...)
        if int(blocknum)%1000 == 0:
            pickle_bids(bids, starttime, blocknum)
    # having finished, save unconditionally
    pickle_bids(bids, starttime, blocknum)

    # print('Cancellation candidates:')
    # print('    ', cancan(bids, endtime = starttime), '(at script start time)')
    # print('    ', cancan(bids, endtime = int(time.time())), '(now)')
    # print('    ', cancan(bids, endtime = int(time.time()) + 60*15), '(in the following fifteen minutes)')
    # print('    ', cancan(bids, endtime = int(time.time()) + 60*60), '(in the following hour)')
    # print('    ', cancan(bids, endtime = int(time.time()) + 60*60*4), '(in the following four hours)')
    # print('    ', cancan(bids, endtime = int(time.time()) + 60*60*24), '(in the following day)')
    # print('    ', cancan(bids, endtime = int(time.time()) + 60*60*24*7), '(in the following seven days)')

    return # main()

if __name__ == '__main__':
    main()
