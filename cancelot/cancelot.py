'''ENS auto-cancellation utils.'''

import pickle
import pprint
import os
import sys
import time

import decimal

from web3 import Web3, IPCProvider
web3 = Web3(IPCProvider()) # TODO: don't use module-level global

nulladdr = '0x0000000000000000000000000000000000000000'
registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
enslaunchblock = 3648565

DAYS19 = 1641600 # bid validity period - 19 days, in seconds

class BidInfo(object):
    '''Information on a single bid and its deed.'''
    def __init__(self, event):
        self.blockplaced = event['blockNumber']
        self.timeplaced = int(web3.eth.getBlock(self.blockplaced)['timestamp'])
        self.timeexpires = self.timeplaced + DAYS19
        self.bidder = '0x' + event['topics'][2][-40:] # 20 bytes from the end
        self.seal = event['topics'][1]
        # these two are not set by default, to save on IPC requests
        self.deedaddr = None
        self.deedsize = None
        
        return

    def __str__(self):
        unit = 'finney'
        self.update_deed_info()

        ret = ''

        ret += 'bidder = "'  + str(self.bidder) + '"; '
        ret += 'seal ="'     + str(self.seal) + '"; '
        ret += '\n'

        ret += 'deedaddr ="' + str(self.deedaddr) + '"; '
        ret += 'deedsize = ' + str(round(
            web3.fromWei(self.deedsize, unit), 2)) + ' (' + unit + ') '
        ret += 'atstake = '  + str(round(
            web3.fromWei(self.deedsize * decimal.Decimal('0.005'), unit), 2)) + ' (' + unit + ') '
        ret += 'expires = ' + str(self.timeexpires) + ' (' + time.ctime(self.timeexpires) + ') '

        return ret

    def update_deed_info(self):
        # look up sealedBids[msg.sender][seal] and its balance
        retval = web3.eth.call({
            'to': registrar,
            'data': '0x5e431709' + '00'*12 + self.bidder[2:] + self.seal[2:]
        })
        self.deedaddr = '0x' + retval[-40:] # 20 bytes from the end

        if self.deedaddr != '0x0000000000000000000000000000000000000000' :
            self.deedsize = int(web3.eth.getBalance(self.deedaddr))
        else:
            self.deedsize = 0 # null-address is not a deed ;)

        return

def print_handled(bidder, seal, action, blocknum, total):
    print('Bid from', bidder, 'with seal', seal, action,
          '(block ' + str(blocknum) + ').', 'Total:', total)

def handle_newbid(bidder, event, bids):
    '''Process NewBid event.'''
    seal = event['topics'][1]
    idx =  bidder + seal
    bids[idx] = BidInfo(event)
    print_handled(bidder, seal, 'added', event['blockNumber'], len(bids))
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

    return bidder + seal

def idx_bidcancelled(event):
    '''Reconstructs our lookup index from logged cancellation event.'''

    seal = event['topics'][1]
    bidder = event['topics'][2][-40:] # 20 bytes from the end

    return '0x' + bidder + seal # TODO: get these '0x' under control, will ya?..

def handle_bidrevealed(bidder, event, bids):
    '''Process BidRevealed event.

    Since BidRevealed and BidCancelled are not differentiated in the temporary
    registrar, they both have to be handled here.'''

    # UGLY: nested exceptions
    try:
        idx = idx_bidrevealed(event, bidder)
        seal = bids[idx].seal
        del bids[idx]
        action = 'revld'
    except KeyError as e:
        # might be "external cancellation", try that...
        try:
            idx = idx_bidcancelled(event)
            seal = bids[idx].seal
            del bids[idx]
            action = 'cancd'
        except KeyError as ee:
            print('='*77 + ' CRAP!!! ' + '='*77)
            print('idx: ', idx_bidcancelled(event))
            print('='*163)
            pprint.pprint(event)
            print('='*163)
            raise ee

    print_handled(bidder, seal, action, event['blockNumber'], len(bids))

    return

# event fingerprint -> handler function
handlers = {
    '0xb556ff269c1b6714f432c36431e2041d28436a73b6c3f19c021827bbdc6bfc29': handle_newbid,
    '0x7b6c4b278d165a6b33958f8ea5dfb00c8c9d4d0acf1985bef5d10786898bc3e7': handle_bidrevealed
}

def check_tx_receipt(receipt, bids):
    logs = receipt['logs']

    # iterate through events, looking for known fingerprints
    for event in logs:
        fp = event['topics'][0]
        handle = handlers[fp] if handlers.get(fp) else None

        # handle matches
        if handle:
            # print('tx', receipt['transactionHash'],
            #       'in block', receipt['blockHash'], '(' + str(receipt['blockNumber']) + ')',
            #       'has event', topic)
            handle(receipt['from'], event, bids)

    return

def check_tx(tx, bids):
    receipt = web3.eth.getTransactionReceipt(tx['hash'])

    # short-circuit if no event logs (probably OOGed)
    if len(receipt['logs']) == 0: return

    check_tx_receipt(receipt, bids)

    return

def load_pickled_bids(filename):
    filename = os.path.realpath(filename)
    print('<<<<< Using pickle', filename)
    # extract from a name like `1495630192-3759000.pickle`
    blocknum = int(filename.split('.')[-2].split('-')[1]) # FIXME: use os.path
    print('<<<<< Set blocknum to:', blocknum)
    with open(filename, 'rb') as fd:
        bids = pickle.load(fd)
        print('<<<<< Loaded', len(bids), 'bids')

    return (bids, blocknum)

def pickle_bids(bids, starttime = None, blocknum = 0):
    if starttime == None:
        starttime = int(time.time())

    # 1495630192-3759000.pickle
    filename = str(starttime) + '-' + str(blocknum) + '.pickle'
    print('>>>>> Writing', len(bids), 'bids to', filename)
    with open(filename, 'wb') as fd:
        pickle.dump(bids, fd, pickle.HIGHEST_PROTOCOL)

    return

def cancan(bids, bythistime = None):
    '''Returns a list of bids that can be cancelled, all the while populating their deed info. '''
    ret = []

    if bythistime == None:
        bythistime = int(time.time())

    for key, bidinfo in bids.items():
        timediff = int(bythistime) - int(bidinfo.timeexpires)

        if timediff >= 0:
            # update deed address and balance
            bidinfo.update_deed_info()

            if bidinfo.deedaddr != nulladdr:
                ret.append(bidinfo)

    return ret

def cancel(bid, from_, to_, gas = 150000, gasprice = None):
    if gasprice == None:
        gasprice = web3.toWei(1, 'shannon')
        print('WARNING: gasprice not specified; forced to', gasprice)

    txhash = web3.eth.sendTransaction({
        'from': from_, 'to': to_, 'gas': gas, 'gasPrice': gasprice,
        'data': '0x9e2ed686' + '00'*12 + bid.bidder[2:] + bid.seal[2:]
    })

    tx = web3.eth.getTransaction(txhash)

    return tx
