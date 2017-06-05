'''ENS auto-cancellation utils.'''

import pickle
import pprint
import os
import random
import sys
import time

import decimal

from web3 import Web3, IPCProvider
web3 = Web3(IPCProvider()) # TODO: don't use module-level global

nulladdr = '0x0000000000000000000000000000000000000000'
registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
enslaunchblock = 3648565

DAYS19 = 1641600 # bid validity period - 19 days, in seconds

# FIXME: account selection
deafaddr = '0xdeaf3515e441067d7f42c2509ec653222537b6eb'
cancelotaddr = '0xC9C7Db3C7a2e3b8AcA6E6F78180F7013575392a3'

def now():
    '''Shorthand.'''
    return int(time.time())

def check_tx_receipt(receipt, bids):
    logs = receipt['logs']

    # iterate through events, looking for known fingerprints
    for event in logs:
        check_event_log(event, bids)

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

# TODO: get from http://ethgasstation.info/hashPowerTable.php
gaspricesinshannon = sorted([1, 4, 16, 18, 20, 27, 40]) # 2017-06-05

def _closest_down(num, sortedlist):
    '''Finds a number closest-down to a given one from a sorted list of numbers.'''
    if num < sortedlist[0]:
        raise Exception('num lower than lowest in list')
    closest = sortedlist[0]

    for i in sortedlist:
        if num - i <= 0:
            break
        closest = i

    return closest

def gasprice_range(bid):
    '''Calculates minimum (recommended) and maximum (absolute) gas price for a given bid.'''
    # magicnums: gas used, determined experimentally
    mingas = 28177 # too late, see tx 0x2a8411294620fb0b5c5bbf710e7aeddbfb48c778c4a8d56e90a7cb51851016d6
    maxgas = 49964 # success,  see tx 0xc9f15d91218b3038946c6839495a8cb63eb4d56e98d25acd913cec3ce4921744
    reward = 0.005 # 0.5%

    bid.update_deed_info()
    if bid.deedaddr == nulladdr:
        raise Exception('Deed cancelled!')

    maximum = int(bid.deedsize * reward / maxgas)

    shannons = _closest_down(web3.fromWei(maximum, 'shannon'), gaspricesinshannon)
    recommended = web3.toWei(shannons, 'shannon')

    return (recommended, maximum)

# TODO: turn into Bid{,Info} class function?..
def cancel_bid(bid, from_, to_ = cancelotaddr, gas = 150000, gasprice = None):
    if gasprice == None:
        gasprice = web3.toWei(12, 'shannon')
        print('WARNING: gasprice not specified; forced to', gasprice)

    txhash = web3.eth.sendTransaction({
        'from': from_,
        'to': to_,
        'gas': gas,
        'gasPrice': gasprice,
        'data': '0x9e2ed686' + '00'*12 + bid.bidder[2:] + bid.seal[2:] # FIXME: magicnums
    })

    return txhash

def one_up(txhash, gasprice = None, maxgasprice = None, sleeptime = 5):
    tx = web3.eth.getTransaction(txhash)

    if gasprice == None:
        gasprice = int(tx['gasPrice'] * 1.11)
        print('WARNING: gasprice not specified; increased by 11% to', gasprice)

    txhash = web3.eth.sendTransaction({
        'nonce': tx['nonce'],
        'from': tx['from'],
        'to': tx['to'],
        'gas': tx['gas'],
        'gasPrice': gasprice,
        'data': tx['input']
    })

    # Keep increasing the gas price, without ever quite reaching the maximum.
    # FIXME: rewrite with generator
    if maxgasprice != None and gasprice < maxgasprice:
        time.sleep(sleeptime)

        gasprice = int(gasprice * 1.11)
        print('DEBUG: increasing gas price to', gasprice)

        try:
            txhash = one_up(txhash, gasprice = gasprice, maxgasprice = maxgasprice)
        except ValueError as e:
            print(e) # DEBUG print for now

    return txhash

# FIXME: generator, async handler
def process_bidlist(bidlist, fromaddr = deafaddr, gpsafe = None, timeoffset = 0):
    '''Runs (sequentially, synchronously) through a list of bids to cancel.'''
    if gpsafe == None:
        gpsafe = web3.toWei(20, 'shannon') # >= 94% of miners

    txhashes = []
    for bid in bidlist:
        # skip bids already cancelled
        try:
            (gprec, gpmax) = gasprice_range(bid)
        except:
            continue

        # FIXME: gas selection - screwed up
        if gpmax < gpsafe:
            gasprice = gprec
        else:
            gasprice = random.randint(min(gpsafe, gprec), max(gpsafe, gprec))

        # FIXME: UGLY stalling
        diff = bid.timeexpires - now() - timeoffset
        if diff > 0:
            # DEBUG
            print('Sleeping for', diff, 'seconds...')
            time.sleep(diff)

        txhash = cancel_bid(bid, fromaddr, gasprice = gasprice)
        txhashes.append(txhash)
        # DEBUG
        print('Submitted', txhash, 'with gas price', web3.fromWei(gasprice, 'shannon'), '(shannon)')

    return txhashes
