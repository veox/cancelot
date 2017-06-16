import decimal
from time import ctime

from . import utils

DAYS19 = 1641600 # bid validity period - 19 days, in seconds

class BidInfo(object):
    '''Information on a single bid and its deed.'''
    def __init__(self, event, web3):
        self.blockplaced = event['blockNumber']
        self.timeplaced = int(web3.eth.getBlock(self.blockplaced)['timestamp'])
        self.timeexpires = self.timeplaced + DAYS19

        self.bidder = '0x' + event['topics'][2][-40:] # 20 bytes from the end
        self.seal = event['topics'][1]

        # save some IPC requests - most bids will be revealed soon, no need to look up
        self.deedaddr = None
        self.deedsize = None
        
        return

    def display(self, web3, unit = 'finney'):
        '''Human-friendly print, multi-line.'''

        # TODO: remove? and require update() be called explicitly
        # make sure printed info is as up-to-date as possible
        self.update(web3)

        ret = ''

        ret += 'bidder = "'  + str(self.bidder) + '"; '
        ret += 'seal ="'     + str(self.seal) + '"; '
        ret += '\n'

        ret += 'deedaddr ="' + str(self.deedaddr) + '"; '
        ret += 'deedsize = ' + str(round(
            web3.fromWei(self.deedsize, unit), 2)) + ' (' + unit + ') '
        ret += 'atstake = '  + str(round(
            web3.fromWei(self.deedsize * decimal.Decimal('0.005'), unit), 2)) + ' (' + unit + ') '
        ret += 'expires = ' + str(self.timeexpires) + ' (' + ctime(self.timeexpires) + ') '

        print(ret)

        return

    def update(self, web3):
        # look up sealedBids[msg.sender][seal] and its balance
        retval = web3.eth.call({
            'to': utils.REGISTRAR,
            'data': '0x5e431709' + '00'*12 + self.bidder[2:] + self.seal[2:]
        })
        self.deedaddr = '0x' + retval[-40:] # 20 bytes from the end

        if self.deedaddr != utils.NULLADDR:
            self.deedsize = int(web3.eth.getBalance(self.deedaddr))
        else:
            self.deedsize = 0 # null-address is not a deed ;)

        return
