#!/usr/bin/env python

import time

from web3 import Web3, IPCProvider

registrar = '0x6090a6e47849629b7245dfa1ca21d94cd15878ef'
startblock = 3648565

web3 = Web3(IPCProvider())

blocknum = startblock
while blocknum <= web3.eth.blockNumber:
    txcount = web3.eth.getBlockTransactionCount(blocknum)
    for i in range(txcount):
        tx = web3.eth.getTransactionFromBlock(blocknum, hex(i))
        if tx['to'] == registrar:
            print('tx', tx['hash'],
                  'in', tx['blockHash'], '(' + str(tx['blockNumber']) + ')',
                  'was to the registrar!')
    
    blocknum += 1
