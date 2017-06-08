Cancelot
========

A bot to cancel bids in the ENS ``.eth`` Registrar that were never revealed.

Overview
--------

The bot is a Python script that connects to a local node over IPC, scans for
placed sealed bids, and tracks which of those haven't been revealed. Once
their expiration timestamp is reached, a call is made to cancel the bid.

The bot is coprophagous in nature, cleaning up the blockchain while
simultaneosly rewarding its operator.

FIXME: Currently not a lib-like package, but a collection of scripts.

FIXME: Several "bidding strategy" helpers made it into the package.

Installation
------------

.. codeblock: sh

   export VIRTUAL_ENV=.virtualenv/cancelot
   mkdir -p $VIRTUAL_ENV
   virtualenv $VIRTUAL_ENV
   source $VIRTUAL_ENV/bin/activate
   pip install -r requirements.txt
   pip install -e . # FIXME: not working yet - not a proper package

Usage
-----

FIXME: Awkward.

Random notes
------------

First direct tx
^^^^^^^^^^^^^^^

On block 3648565:

https://etherscan.io/tx/0x6e032eed213f1a641af8cdb7fd3770984010a38c04f6c06e393b03dfca30a80d

First reveal?..
^^^^^^^^^^^^^^^

Bid from 0x3c12c57a05780b6e97360392ce18f1ad92fbe0a7 with seal 0x844e77749af1a22536ebbe7fed28588cc4e82302096105f0309db00dd8c79256 added (block 3665634).
'0x3c12c57a05780b6e97360392ce18f1ad92fbe0a7', '0x00033095b0df8983c66c84b7ff557a5b9b4705a9e22167ae748351d6357ae98b'

First cancel?..
^^^^^^^^^^^^^^^

Bid from 0x3e1f4f4de69e7e2cec0f45153a542d6108ef81bb with seal 0x486e1b9e1e85a60199f98c945ae548c42c51b472b8842181c1d1414a01a4f97c cancd (block 3754090).

Something weird!
^^^^^^^^^^^^^^^^

Possibly a multisig contract doing the bidding?..

WARNING! Key not found in store, skipping bid removal! Tried:
('bytes32 not in store', '0x3e35de8f9a0f71c7891245f50a46be4e863244a4', '0x772f91f480a2292645cedee795ffd0f03793e580ba481c16ad23c7b7d0b7f1d6')
('bytes32 not in store', '0x3e35de8f9a0f71c7891245f50a46be4e863244a4', '0x0fb37976806ab1a28e0b52bc3b81a240298f3859b560a5b74c08a9fadd21b818')
--
WARNING! Key not found in store, skipping bid removal! Tried:
('bytes32 not in store', '0x3e35de8f9a0f71c7891245f50a46be4e863244a4', '0x9d2c5cb0cbd9397dbe1b448b1c286f93ee7f51b13c9668bffdd09a22fa3033ba')
('bytes32 not in store', '0x3e35de8f9a0f71c7891245f50a46be4e863244a4', '0x0fb37976806ab1a28e0b52bc3b81a240298f3859b560a5b74c08a9fadd21b818')
