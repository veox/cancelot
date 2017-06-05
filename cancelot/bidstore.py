from bidinfo import Bidinfo

def _print_handled(bidder, seal, action, blocknum, total):
    print('Bid from', bidder, 'with seal', seal, action,
          '(block ' + str(blocknum) + ').', 'Total:', total)
    return

class BidStore(object):
    '''Multiple-BidInfo store with indexed look-up.'''
    def __init__(self, web3):
        '''Creates an empty dictionary for storage, and assigns default handlers.'''

        self.web3 = web3
        self.store = {}
        self.handlers = {
            '0x7b6c4b278d165a6b33958f8ea5dfb00c8c9d4d0acf1985bef5d10786898bc3e7': self._rem, # BidRevealed
            '0xb556ff269c1b6714f432c36431e2041d28436a73b6c3f19c021827bbdc6bfc29': self._add  # NewBid
        }

        return

    def handle_events(self, events: list):
        '''Wrapper to process a list of events.'''

        for ev in events:
            self.handle_event(ev)

        return

    def handle_event(self, event: dict):
        '''Changes store based on type of event.'''

        fp = event['topics'][0]
        handler = self.handlers[fp] if self.handlers.get(fp) else None

        if handler:
            # got match - handle as specified
            handler(event)
        else:
            # unhandled events are currently allowed
            pass

        return

    # TODO: rework indexing for same-pair bidder+seal bids
    def _key_from_bidinfo(bid: BidInfo):
        return bid.bidder + bid.seal

    def _key_from_reveal_event(event: dict):
        '''Reconstructs our lookup index from logged timely reveal event.'''

        bidder = FIXME

        # salt is not logged, so must be reconstructed from transaction
        tx = self.web3.eth.getTransaction(event['transactionHash'])
        # get salt from transaction data - it's not logged :/
        salt = '0x' + tx['input'][-64:] # 32 bytes from the end
        # get value from here, too - logged one might be changed due to `value = min(_value, bid.value())`
        OFFSET = 2+8+64 # 2 for '0x', 8 for function signature, 64 for bytes(32).hex() hash
        value = '0x' + tx['input'][OFFSET:OFFSET+64]
        # get other from logged event (FIXME: get from tx, too?.. what the hell...)
        thishash = event['topics'][1]
        # calculate seal (used as part of index)
        seal = self.web3.sha3('0x' + thishash[2:] + bidder[2:] + value[2:] + salt[2:])

        return bidder + seal

    # FIXME: less rigid indexing
    def _key_from_cancel_event(event: dict):
        '''Reconstructs our lookup index from logged cancellation event.'''

        seal = event['topics'][1] # with '0x' up front
        bidder = event['topics'][2][-40:] # 20 bytes from the end

        return '0x' + bidder + seal

    def _add(self, event):
        '''Process NewBid event.'''

        bid = BidInfo(event)
        key = _key_from_bidinfo(bid)

        if self.store.get(key):
            print('WARNING! Writing over existing key', key, 'in store!')
        self.store[key] = bid

        # DEBUG
        _print_handled(bid.bidder, bid.seal, 'added', bid.timeplaced, len(self.store))

        return

    def _rem(self, event):
        '''Process BidRevealed event.

        Since BidRevealed and BidCancelled are not differentiated in the temporary
        registrar, they both have to be handled here.'''

        bidder = FIXME
        bid = FIXME

        try:
            key = _key_from_reveal_event(event)
            seal = self.store[key].seal # might raise KeyError
            action = 'revld'
        except KeyError:
            # might be "external cancellation", try that...
            key = _key_from_cancel_event(event)
            seal = self.store[key].seal
            action = 'cancd'
        finally:
            del bids[key]

        # DEBUG
        _print_handled(bidder, seal, action, event['blockNumber'], len(bids))

        return bid
