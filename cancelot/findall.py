#!/usr/bin/env python
# find all transactions with a specific "fingerprint" in logs

import pprint
import time

from web3 import Web3, IPCProvider
web3 = Web3(IPCProvider())

registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
startblock = 3648565

class BidInfo(object):
    def __init__(self, event):
        self.timeexpires = web3.eth.getBlock(event['blockNumber'])['timestamp'] + 1209600 # magicnum: 2 weeks
        self.bidder = event['topics'][2]
        self.seal = event['topics'][1]
        return

# msg.sender+sealedBid -> bid info
bids = {}

def handle_newbid(bidder, event):
    seal = event['topics'][1]
    idx =  bidder + seal
    bids[idx] = BidInfo(event)
    print('Bid from', bidder, 'with seal', seal, 'added',
          '(block ' + str(event['blockNumber']) + ').', 'Total:', len(bids))
    return

def idx_bidcancelled(event):
    seal = event['topics'][1]
    bidder = event['topics'][2][-40:] # 20 bytes from the end
    return bidder + seal

def handle_bidrevealed(bidder, event):
    # FIXME: we've already retrieved this before!
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
    idx = bidder + seal

    # FIXME: ugly nested
    try:
        del bids[idx]
    except KeyError as e:
        # might be "external cancellation", try that...
        try:
            del bids[idx_bidcancelled(event)]
        except KeyError as ee:
            print('='*77 + ' CRAP!!! ' + '='*77)
            print('idx:     ', idx_bidcancelled(event))
            print('='*163)
            pprint.pprint(event)
            print('='*163)
            raise ee
        # print('='*77 + ' DANG!.. ' + '='*77)
        # print('thishash:', thishash)
        # print('bidder:  ', bidder)
        # print('value:   ', value)
        # print('salt:    ', salt)
        # print('seal:    ', seal)
        # print('idx:     ', idx)
        # print('='*163)
        # pprint.pprint(tx)
        # print('='*163)
        # raise e

    print('Bid from', bidder, 'with seal', seal, 'remvd',
          '(block ' + str(event['blockNumber']) + ').', 'Total:', len(bids))
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

def check_receipt_for_topics(receipt, topics):
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
            handlers[topic](receipt['from'], event)
    return

def check_tx(tx):
    receipt = web3.eth.getTransactionReceipt(tx['hash'])

    # short-circuit if no event logs (probably OOGed)
    if len(receipt['logs']) == 0: return

    check_receipt_for_topics(receipt, topics)

    return


#
now = int(time.time())

# read in
blocknum = startblock - 1
while blocknum <= web3.eth.blockNumber:
    blocknum += 1
    txcount = web3.eth.getBlockTransactionCount(blocknum)
    if txcount == 0: continue

    # iterate over transactions
    for txi in range(txcount):
        tx = web3.eth.getTransactionFromBlock(blocknum, hex(txi))
        if tx['to'] == registrar:
            check_tx(tx)

# print those that have not been revealed
cancan = 0
for _, bidinfo in bids.iteritems():
    if now - int(bidinfo.timeexpires) < 0:
        cancan += 1
        print('Bid can be cancelled:', bidinfo.bidder, bidinfo.seal)
print('Total:', cancan)
