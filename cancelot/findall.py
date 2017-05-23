#!/usr/bin/env python
# find all transactions with a specific "fingerprint" in logs

import time

from web3 import Web3, IPCProvider

registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
startblock = 3648565

# topic fingerprints
fp_auctionstarted = '0x87e97e825a1d1fa0c54e1d36c7506c1dea8b1efd451fe68b000cf96f7cf40003'
fp_newbid = '0xb556ff269c1b6714f432c36431e2041d28436a73b6c3f19c021827bbdc6bfc29'
fp_bidrevealed = '0x7b6c4b278d165a6b33958f8ea5dfb00c8c9d4d0acf1985bef5d10786898bc3e7'


web3 = Web3(IPCProvider())

def check_tx(tx):
    receipt = web3.eth.getTransactionReceipt(tx['hash'])
    logs = receipt['logs']

    # skip tx if no event logs (probably OOGed)
    if len(logs) == 0: continue

    # iterate through events, looking for bids placed/revealed fingerprint
    for l in logs:
        fp = l['topics'][0]
        if fp == fp_newbid:
            print('tx', tx['hash'],
                  'in', tx['blockHash'], '(' + str(tx['blockNumber']) + ')',
                  'placed a bid')
        if fp == fp_bidrevealed:
            print('tx', tx['hash'],
                  'in', tx['blockHash'], '(' + str(tx['blockNumber']) + ')',
                  'revealed a bid')
    return


blocknum = startblock
while blocknum <= web3.eth.blockNumber:
    txcount = web3.eth.getBlockTransactionCount(blocknum)
    if txcount == 0: continue
    # iterate over transactions
    for txi in range(txcount):
        tx = web3.eth.getTransactionFromBlock(blocknum, hex(txi))
        if tx['to'] == registrar:
            check_tx(tx)

    blocknum += 1
