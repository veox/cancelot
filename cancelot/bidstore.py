# FIXME: refs to web3 object

import pprint # debug-print on exception

import bidinfo

def _print_handled(bidder, seal, action, blocknum, total):
    print('Bid from', bidder, 'with seal', seal, action,
          '(block ' + str(blocknum) + ').', 'Total:', total)
    return

# FIXME: less rigid indexing
def _idx_bidrevealed(event, bidder): # FIXME: don't pass `bidder`
    '''Reconstructs our lookup index from logged timely reveal event.'''

    # FIXME: we've already retrieved this before, way down in the stack!
    tx = web3.eth.getTransaction(event['transactionHash'])
    # get salt from transaction data - it's not logged :/
    salt = '0x' + tx['input'][-64:] # 32 bytes from the end
    # get value from here, too - logged one might be changed due to `value = min(_value, bid.value())`
    OFFSET = 2+8+64 # 2 for '0x', 8 for function signature, 64 for bytes(32).hex() hash
    value = '0x' + tx['input'][OFFSET:OFFSET+64]
    # get other from logged event (FIXME: get from tx, too?.. what the hell...)
    thishash = event['topics'][1]
    # calculate seal (used as part of index)
    seal = web3.sha3('0x' + thishash[2:] + bidder[2:] + value[2:] + salt[2:])

    return bidder + seal

# FIXME: less rigid indexing
def _idx_bidcancelled(event):
    '''Reconstructs our lookup index from logged cancellation event.'''

    seal = event['topics'][1]
    bidder = event['topics'][2][-40:] # 20 bytes from the end

    return '0x' + bidder + seal # FIXME: hard-coded indexing pattern

def _handle_newbid(event, bids):
    '''Process NewBid event.'''
    bid = bidinfo.BidInfo(event)
    idx =  bid.bidder + bid.seal # FIXME: hard-coded indexing pattern
    bids[idx] = bid
    print_handled(bid.bidder, bid.seal, 'added', event['blockNumber'], len(bids))
    return

def _handle_bidrevealed(bidder, event, bids):
    '''Process BidRevealed event.

    Since BidRevealed and BidCancelled are not differentiated in the temporary
    registrar, they both have to be handled here.'''

    # UGLY: nested exceptions
    try:
        idx = _idx_bidrevealed(event, bidder)
        seal = bids[idx].seal
        del bids[idx]
        action = 'revld'
    except KeyError as e:
        # might be "external cancellation", try that...
        try:
            idx = _idx_bidcancelled(event)
            seal = bids[idx].seal
            del bids[idx]
            action = 'cancd'
        except KeyError as ee:
            print('='*77 + ' CRAP!!! ' + '='*77)
            print('idx: ', _idx_bidcancelled(event))
            print('='*163)
            pprint.pprint(event)
            print('='*163)
            raise ee

    print_handled(bidder, seal, action, event['blockNumber'], len(bids))

    return


# event fingerprint -> handler function
_handlers = {
    '0xb556ff269c1b6714f432c36431e2041d28436a73b6c3f19c021827bbdc6bfc29': _handle_newbid,
    '0x7b6c4b278d165a6b33958f8ea5dfb00c8c9d4d0acf1985bef5d10786898bc3e7': _handle_bidrevealed
}

class BidStore(object):
    '''Multiple-BidInfo store with indexed look-up.'''
    def __init__(self):
        '''Creates an empty dictionary for storage, and assigns default handlers.'''

        self.store = {}
        self.handlers = _handlers

        return

    def handle_events(self, events):
        '''Wrapper to process a list of events.'''

        if type(events) is not list:
            raise TypeError('Expecting a list (of dicts)!')

        for ev in events:
            self.handle_event(ev)

        return

    def handle_event(self, ev):
        '''Changes store based on type of event.'''

        fp = ev['topics'][0]
        handler = self.handlers[fp] if self.handlers.get(fp) else None # TODO: handler managing?

        if handler:
            # got match - handle as specified
            handler(ev, self.store) # FIXME: passing store around :/
        else:
            # unhandled events are currently allowed
            pass

        return
