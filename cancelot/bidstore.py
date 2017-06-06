from .bidinfo import BidInfo

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
        self._size = 0
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

    def get(self, key: tuple):
        '''Returns BidInfo for given (bidder, seal) key.'''

        (bidder, seal) = key

        if not self.store.get(bidder):
            raise Exception('Requested to get entry but bidder is not present!', bidder, seal)
        if not self.store[bidder].get(seal):
            raise Exception('Requested to get entry but seal is not present!', bidder, seal)

        return self.store[bidder][seal]

    def set(self, key: tuple, bi: BidInfo):
        '''Sets a BidInfo for a given (bidder, seal) key.'''

        (bidder, seal) = key

        # create bidder entry if it doesn't exist
        if not self.store.get(bidder):
            self.store[bidder] = {}
        # increase size counter if not rewriting
        if not self.store[bidder].get(seal):
            self._size += 1
        # link the bid info unconditionally
        self.store[bidder][seal] = bi

        return

    def unset(self, key: tuple):
        '''Deletes a Bidinfo from the store.'''

        (bidder, seal) = key

        if not self.store.get(bidder):
            raise Exception('Requested to remove entry but bidder is not present!', bidder, seal)
        if not self.store[bidder].get(seal):
            raise Exception('Requested to remove entry but seal is not present!', bidder, seal)

        # clear bid info...
        del self.store[bidder][seal]
        self._size -= 1
        # ... and perhaps the bidder entry, if it's empty
        if not self.store[bidder]:
            del self.store[bidder]

        return

    # TODO: rework indexing for same-pair bidder+seal bids
    def _key_from_bidinfo(self, bid: BidInfo):
        return (bid.bidder, bid.seal)

    def _key_from_reveal_event(self, event: dict):
        '''Reconstructs our lookup index from logged timely reveal event.'''

        bidder = '0x' + event['topics'][2][-40:] # 20 bytes off the end

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

        return (bidder, seal)

    # FIXME: less rigid indexing
    def _key_from_cancel_event(self, event: dict):
        '''Reconstructs our lookup index from logged cancellation event.'''

        seal = event['topics'][1] # with '0x' up front
        bidder = '0x' + event['topics'][2][-40:] # 20 bytes off the end

        return (bidder, seal)

    def _add(self, event):
        '''Process NewBid event.'''

        bid = BidInfo(event, self.web3)
        key = self._key_from_bidinfo(bid)

        presize = self._size
        self.set(key, bid)
        if presize == self._size:
            print('WARNING! Store size has not changed on write!')

        # DEBUG
        _print_handled(bid.bidder, bid.seal, 'added', bid.blockplaced, self._size)

        return

    def _rem(self, event):
        '''Process BidRevealed event.

        Since BidRevealed and BidCancelled are not differentiated in the temporary
        registrar, looking up the key for both has to be attempted here.'''

        try:
            key = self._key_from_reveal_event(event)
            bid = self.get(key) # may throw Exception
            action = 'revld'
        except Exception:
            # might be "external cancellation", try that...
            key = self._key_from_cancel_event(event)
            bid = self.get(key)
            action = 'cancd'
        finally:
            # get immutable copies (str)
            bidder = bid.bidder
            seal = bid.seal
            # clear bid object
            self.unset(key)

        # DEBUG
        _print_handled(bidder, seal, action, event['blockNumber'], self._size)

        return
