#!/usr/bin/env python
# find all transactions with a specific "fingerprint" in logs

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

# msg.sender+sealedBid -> deed info
bids = {}

# TODO: can be replaced by lambdas in `handlers` when proven to work
def handle_newbid(idx, event):
    bids[idx] = BidInfo(event)
    print('Bid', idx, 'added', '(block ' + str(event['blockNumber']) + ').', 'Total:', len(bids))
    return
def handle_bidrevealed(idx, event):
    del bids[idx]
    print('Bid', idx, 'removed', '(block ' + str(event['blockNumber']) + ').', 'Total:', len(bids))
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
            idx = receipt['from'] + event['topics'][1]
            handlers[topic](idx, event)
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
for _, bidinfo in bids.iteritems():
    if now - int(bidinfo.timeexpires) < 0:
        print('Bid could be cancelled:', bidinfo.bidder, bidinfo.seal)
