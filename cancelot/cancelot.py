#!/usr/bin/env python

import time

from web3 import Web3, IPCProvider
# TODO: use `esper` for entity tracking?

registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
startblock = 3648565

web3 = Web3(IPCProvider())


def new_block_callback(block_hash):
    print('Block ', block_hash, '(' + str(web3.eth.blockNumber) + ')')
    
    # ========= TODO =========
    # take some earlier block (to avoid chain reorg fuzzies)
    #  scan for `placeBid()` and `startAuctionAndBid()` (or `NewBid` events?..)
    #   add deed to tracked list, along with bidder address, seal, and expiration timestamp
    #  scan for `revealBid()` and `cancelBid()` (or appropriate events?..)
    #   remove revealed/cancelled bids' deeds from tracked list
    # for each expired deed
    #  check if it has _just_ been cancelled (destroyed) -- eth.getCode() == '0x'?..
    #   send a cancellation tx
    #   remove deed from tracked list, unconditionally

    return


new_block_filter = web3.eth.filter('latest')
new_block_filter.watch(new_block_callback)

while True:
    time.sleep(1)
