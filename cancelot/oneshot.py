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

registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
enslaunchblock = 3648565

DAYS19 = 1641600 # bid validity period - 19 days, in seconds

class BidInfo(object):
    def __init__(self, event):
        self.blockadded = event['blockNumber']
        self.timeadded = int(web3.eth.getBlock(self.blockadded)['timestamp'])
        self.timeexpires = self.timeadded + DAYS19
        self.bidder = '0x' + event['topics'][2][-40:] # 20 bytes from the end
        self.seal = event['topics'][1]
        return

def handle_newbid(bidder, event, bids):
    seal = event['topics'][1]
    idx =  bidder + seal
    bids[idx] = BidInfo(event)
    print('Bid from', bidder, 'with seal', seal, 'added',
          '(block ' + str(event['blockNumber']) + ').', 'Total:', len(bids))
    return

def idx_bidrevealed(event, bidder):
    '''Reconstructs our lookup index from logged timely reveal event.'''
    # FIXME: we've already retrieved this before, way down in the stack!
    tx = web3.eth.getTransaction(event['transactionHash'])
    # get salt from transaction data - it's not logged :/
    salt = '0x' + tx['input'][-64:] # 32 bytes from the end
    # get value from here, too - logged one might be changed due to `value = min(_value, bid.value())`
    _offset = 2+8+64 # 2 for '0x', 8 for function signature, 64 for bytes(32).hex() hash
    value = '0x' + tx['input'][_offset:_offset+64]
    # get other from logged event (FIXME: get from tx, too?.. what the hell...)
    thishash = event['topics'][1]
    # calculate seal (used as part of index)
    seal = web3.sha3('0x' + thishash[2:] + bidder[2:] + value[2:] + salt[2:])
    # finally, formulate it
    return bidder + seal

def idx_bidcancelled(event):
    '''Reconstructs our lookup index from logged cancellation event.'''
    seal = event['topics'][1]
    bidder = event['topics'][2][-40:] # 20 bytes from the end
    return '0x' + bidder + seal # TODO: get these '0x' under control, will ya?..

# TODO: idx_bidrevealed()

def handle_bidrevealed(bidder, event, bids):
    # FIXME: ugly - nested exceptions
    try:
        idx = idx_bidrevealed(event, bidder)
        seal = bids[idx].seal
        del bids[idx]
        print('Bid from', bidder, 'with seal', seal, 'remvd',
              '(block ' + str(event['blockNumber']) + ').', 'Total:', len(bids))
    except KeyError as e:
        # might be "external cancellation", try that...
        try:
            idx = idx_bidcancelled(event)
            seal = bids[idx].seal
            del bids[idx]
            print('Bid from', bidder, 'with seal', seal, 'cancd',
                  '(block ' + str(event['blockNumber']) + ').', 'Total:', len(bids))
        except KeyError as ee:
            print('='*77 + ' CRAP!!! ' + '='*77)
            print('idx: ', idx_bidcancelled(event))
            print('='*163)
            pprint.pprint(event)
            print('='*163)
            raise ee
    return

# fingerprint -> event name
topics = {
    #'0x87e97e825a1d1fa0c54e1d36c7506c1dea8b1efd451fe68b000cf96f7cf40003': 'AuctionStarted',
    '0xb556ff269c1b6714f432c36431e2041d28436a73b6c3f19c021827bbdc6bfc29': 'NewBid',
    '0x7b6c4b278d165a6b33958f8ea5dfb00c8c9d4d0acf1985bef5d10786898bc3e7': 'BidRevealed'
}
# event name -> handler function
handlers = {
    'NewBid': handle_newbid,
    'BidRevealed': handle_bidrevealed
}

def check_receipt_for_topics(receipt, topics, bids):
    logs = receipt['logs']
    # iterate through events, looking for bids placed/revealed fingerprint
    for event in logs:
        fp = event['topics'][0]
        topic = topics[fp] if topics.get(fp) else False
        # handle matches
        if topic:
            # print('tx', receipt['transactionHash'],
            #       'in block', receipt['blockHash'], '(' + str(receipt['blockNumber']) + ')',
            #       'has event', topic)
            handlers[topic](receipt['from'], event, bids)
    return

def check_tx(tx, bids):
    receipt = web3.eth.getTransactionReceipt(tx['hash'])

    # short-circuit if no event logs (probably OOGed)
    if len(receipt['logs']) == 0: return

    check_receipt_for_topics(receipt, topics, bids)

    return

def load_pickled_bids(filename):
    print('<<<<< Using pickle', filename)
    # extract from a name like `1495630192-3759000.pickle`
    blocknum = int(filename.split('.')[0].split('-')[1])
    print('<<<<< Set blocknum to', blocknum)
    with open(filename, 'rb') as fd:
        bids = pickle.load(fd)
        print('<<<<< Loaded', len(bids), 'bids')
    return bids, blocknum # FIXME: hidden return of `blocknum`

def pickle_bids(bids, starttime = int(time.time()), blocknum = 0):
    # 1495630192-3759000.pickle
    filename = str(starttime) + '-' + str(blocknum) + '.pickle'
    print('>>>>> Writing', len(bids), 'bids to', filename)
    with open(filename, 'wb') as fd:
        pickle.dump(bids, fd, pickle.HIGHEST_PROTOCOL)
    return

def cancan(bids, endtime = int(time.time())):
    cancan = 0
    for _, bidinfo in bids.items():
        timediff = int(endtime) - int(bidinfo.timeexpires)
        if timediff >= 0:
            cancan += 1
            # look up sealedBids[msg.sender][seal]
            retval = web3.eth.call({
                'to': registrar,
                'data': '0x5e431709' + '00'*12 + bidinfo.bidder[2:] + bidinfo.seal[2:]
            })
            deedaddr = '0x' + retval[-40:] # 20 bytes from the end
            atstake = web3.fromWei(web3.eth.getBalance(deedaddr), 'finney') * decimal.Decimal('0.005') # 0.5%
            print('Can cancel! bidder:', bidinfo.bidder, 'seal:', bidinfo.seal,
                  'timediff:', timediff, 'at stake:', round(atstake, 2), '(finneys)')
    return cancan

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

    print('Cancellation candidates:')
    print('    ', cancan(bids, endtime = starttime), '(at script start time)')
    print('    ', cancan(bids, endtime = int(time.time())), '(now)')
    print('    ', cancan(bids, endtime = int(time.time()) + 60*15), '(in the following fifteen minutes)')
    print('    ', cancan(bids, endtime = int(time.time()) + 60*60), '(in the following hour)')
    print('    ', cancan(bids, endtime = int(time.time()) + 60*60*4), '(in the following four hours)')
    print('    ', cancan(bids, endtime = int(time.time()) + 60*60*24), '(in the following day)')
    print('    ', cancan(bids, endtime = int(time.time()) + 60*60*24*7), '(in the following seven days)')

    return # main()

if __name__ == '__main__':
    main()
