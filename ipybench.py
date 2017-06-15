#!/usr/bin/env python
# WIP ipython bench generic imports and setup

import copy
import pprint
import random
import time

import cancelot

from web3 import Web3, IPCProvider
web3 = Web3(IPCProvider())

# TODO: move to utils?
def clear_tx(txhash, gasprice = None):
    '''Resend transaction with high gas price, low gas and no data.'''

    tx = web3.eth.getTransaction(txhash)
    if not tx:
        return

    if gasprice == None:
        gasprice = web3.toWei(20, 'shannon')
        print('WARNING: gasprice not specified; set to', gasprice)

    txhash = web3.eth.sendTransaction({
        'nonce': tx['nonce'],
        'from': tx['from'],
        'to': tx['to'],
        'gas': 21000,
        'gasPrice': gasprice,
        'data': '0x'
    })

    return txhash

# TODO: turn into Bid{,Info} class function?..
def cancel_bid(bid, from_, to_ = cancelot.utils.CANCELOTADDR, gas = 150000, gasprice = None):
    if gasprice == None:
        gasprice = web3.toWei(20, 'shannon')
        print('WARNING: gasprice not specified; forced to', gasprice)

    txhash = web3.eth.sendTransaction({
        'from': from_,
        'to': to_,
        'gas': gas,
        'gasPrice': gasprice,
        'data': '0x9e2ed686' + '00'*12 + bid.bidder[2:] + bid.seal[2:] # FIXME: magicnums
    })

    return txhash

# FIXME: not actually "one-up", since blocking and recursive
def one_up(txhash, gasprice = None, maxgasprice = None, sleeptime = 0):
    '''TODO: desc'''

    time.sleep(sleeptime)

    tx = web3.eth.getTransaction(txhash)

    # short-circuit if tx no longer pending
    if not tx:
        return txhash

    if gasprice == None:
        gasprice = int(tx['gasPrice'] * 1.101) # magicnum: 10.1% (slightly above geth default 10%)
        print('WARNING: gasprice not specified; increased by 11% to', gasprice)

    # replace transaction once
    txhash = web3.eth.sendTransaction({
        'nonce': tx['nonce'],
        'from': tx['from'],
        'to': tx['to'],
        'gas': tx['gas'],
        'gasPrice': gasprice,
        'data': tx['input']
    })
    print('DEBUG: submitted', txhash, 'with gas price increased to', gasprice)

    # Keep increasing the gas price, without ever quite reaching the maximum.
    # FIXME: recursive; rewrite as generator?..
    nextgasprice = int(gasprice * 1.101) # magicnum: 10.1% (slightly above geth default 10%)
    if maxgasprice != None and nextgasprice < maxgasprice:
        # magicnum 16: about one block
        txhash = one_up(txhash, gasprice = nextgasprice, maxgasprice = maxgasprice, sleeptime = 16)

    return txhash

# FIXME: do generator, async handler
def process_bidlist(bidlist, fromaddr, gpsafe = None, timeoffset = 0, timetosleep = 8):
    '''Runs (sequentially, synchronously) through a list of bids to cancel.'''

    if gpsafe == None:
        gpsafe = web3.eth.gasPrice

    txhashes = []

    for bid in bidlist:
        print('Next bid:')
        bid.display(web3)

        try:
            (gprec, gpmax) = cancelot.utils.gasprice_range(bid)
        except Exception as e:
            print(e)
            continue
        # magicnum 42: safeguard from giving all to miners
        gpmax = min(gpmax, web3.toWei(42, 'shannon') + random.randint(0, 1000000))

        # FIXME: UGLY stalling
        diff = bid.timeexpires - cancelot.utils.now() + timeoffset
        if diff > 0:
            print('Sleeping for', diff, 'seconds...') # DEBUG
            time.sleep(diff)

        print('Placing initial tx with gasprice', gpsafe) # DEBUG
        txhash = cancel_bid(bid, fromaddr, cancelot.utils.CANCELOTADDR, gasprice = gpsafe)

        # increase tx gas price if still within limits
        if gpsafe < gpmax:
            try:
                txhash = one_up(txhash, maxgasprice = gpmax, sleeptime = timetosleep)
            except Exception as e:
                print(e)

        txhashes.append(txhash)

        # DEBUG
        tx = web3.eth.getTransaction(txhash)
        try:
            finalgp = tx['gasPrice']
        except:
            print('OOPS! tx bogus!')
            print('txhash:', txhash)
            finalgp = 42 # magicnum 42: a nice, round number

        print('Final tx ', txhash, 'with gas price', web3.fromWei(finalgp, 'shannon'), '(shannon)')

    return txhashes

# TODO: pass selector function as argument?
def watch_these(bidlist, minfinney = 0.05, maxfinney = 1000000000):
    '''TODO: bidlist'''

    ret = []

    for bid in sorted(bidlist, key=lambda x: x.timeexpires):
        atstake = bid.deedsize * 0.005
        if atstake >= web3.toWei(minfinney, 'finney') and atstake < web3.toWei(maxfinney, 'finney'):
            ret.append(copy.copy(bid))

    return ret

bids = cancelot.BidStore(web3)
(bidstore, blocknum) = cancelot.utils.load_pickled_bids('pickles/latest.pickle')
bids.store = bidstore

now = cancelot.utils.now()
until = now + 24*60*60

cc = bids.cancan(until)

ccc = watch_these(cc)
