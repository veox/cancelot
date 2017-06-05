'''Utility functions bordering on bidding strategy (should be removed?).'''

# FIXME: refs to web3 object

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