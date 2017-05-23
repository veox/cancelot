#!/usr/bin/env python
# find all transactions with a specific "fingerprint" in logs

import time

from web3 import Web3, IPCProvider

registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
startblock = 3648565

def handle_newbid(receipt):
    print('STUB newbid')
    return

def handle_bidrevealed(receipt):
    print('STUB bidrevealed')
    return

# topics: fingerprints -> event name
topics = {
    #'0x87e97e825a1d1fa0c54e1d36c7506c1dea8b1efd451fe68b000cf96f7cf40003': 'AuctionStarted',
    '0xb556ff269c1b6714f432c36431e2041d28436a73b6c3f19c021827bbdc6bfc29': 'NewBid',
    '0x7b6c4b278d165a6b33958f8ea5dfb00c8c9d4d0acf1985bef5d10786898bc3e7': 'BidRevealed'
}
handlers = {
    'NewBid': handle_newbid,
    'BidRevealed': handle_bidrevealed
}

def check_receipt_for_topics(receipt, topics):
    logs = receipt['logs']
    # iterate through events, looking for bids placed/revealed fingerprint
    for entry in logs:
        fp = entry['topics'][0]
        topic = topics[fp] if topics.get(fp) else False
        # handle matches
        if topic:
            print('tx', receipt['transactionHash'],
                  'in block', receipt['blockHash'], '(' + str(receipt['blockNumber']) + ')',
                  'has event', topic)
            handlers[topic](receipt)
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
