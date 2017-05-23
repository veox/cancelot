#!/usr/bin/env python
# find all transactions with a specific "fingerprint" in logs

import time

from web3 import Web3, IPCProvider

registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
startblock = 3648565

class DeedInfo(object):
    def __init__(self, deedaddr):
        self.created = TODO()
        self.expires = TODO()
        self.bidder = TODO()
        self.seal = TODO()
        return

# deed address -> deed info
deeds = {}

def get_deed_address(msgsender, seal):
    return MAGIC(registrar.sealedBids[msg.sender][seal])

def handle_newbid(event):
    deedaddr = get_deed_address(event['from'], event['topics'][1])
    deeds[deedaddr] = DeedInfo(deedaddr)
    return

def handle_bidrevealed(event):
    deedaddr = get_deed_address(event['from'], event['topics'][1])
    del deeds[deedaddr]
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
            handlers[topic](event)
    return

web3 = Web3(IPCProvider())

def check_tx(tx):
    receipt = web3.eth.getTransactionReceipt(tx['hash'])

    # short-circuit if no event logs (probably OOGed)
    if len(receipt['logs']) == 0: return

    check_receipt_for_topics(receipt, topics)

    return


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
