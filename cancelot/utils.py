'''ENS auto-cancellation utils.'''

import pickle
import pprint
import os
import random
import sys
import time

import decimal

# FIXME: module-level web3
from web3 import Web3, IPCProvider
web3 = Web3(IPCProvider()) # TODO: don't use module-level global

from .bidstore import BidStore

NULLADDR = '0x0000000000000000000000000000000000000000'
REGISTRAR = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
ENSLAUNCHBLOCK = 3648565

# FIXME: hard-coded
CANCELOTADDR = '0xC9C7Db3C7a2e3b8AcA6E6F78180F7013575392a3'

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
        starttime = now()

    # 1495630192-3759000.pickle
    filename = str(starttime) + '-' + str(blocknum) + '.pickle'
    # FIXME: assumption that `bids` is a `BidStore.store`
    print('>>>>> Writing bids to', filename)

    with open(filename, 'wb') as fd:
        pickle.dump(bids, fd, pickle.HIGHEST_PROTOCOL)
    print('>>>>> Done!')

    return

def cancan(bidstore: BidStore, bythistime = None):
    '''Returns a list of bids that can be cancelled, all the while populating their deed info. '''
    ret = []

    if bythistime == None:
        bythistime = now()

    for bidder, seals in bidstore.store.items():
        for seal, bidinfo in seals.items():
            timediff = bythistime - bidinfo.timeexpires

            # to save on IPC queries, only update if can cancel in specified period
            if timediff >= 0:
                key = (bidder, seal)
                bidstore.update(key)

                if bidinfo.deedaddr != NULLADDR:
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

    bid.update_deed_info(web3)
    if bid.deedaddr == NULLADDR:
        raise Exception('Deed cancelled!')

    maximum = int(bid.deedsize * reward / maxgas)

    shannons = _closest_down(web3.fromWei(maximum, 'shannon'), gaspricesinshannon)
    recommended = web3.toWei(shannons, 'shannon')

    return (recommended, maximum)
