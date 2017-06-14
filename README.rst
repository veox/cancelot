Cancelot
========

A set of utilities for cancelling bids in the ENS ``.eth`` Registrar that
were never revealed.

The code is released as-is, without warranty of any kind, including
fitness for a purpose.

Do not read past this line.

You have been warned!..


Overview
--------

The utilities allow to scan for placed sealed bids, and to determine
which of those haven't been revealed yet. Once their expiration
timestamp is reached, a call can be made to cancel such bids.

This allows implementing a bot that cleans up the blockchain and,
if efficient, also rewards its operator.

An IPC connection to a local node is required.

The on-chain component is written in Solidity, with the primary
consideration being low gas price for calls.

You can `see it at work`_ on a block explorer. While there, take a look
`at a competitor`_, too.

.. _see it at work: https://etherscan.io/address/0xc9c7db3c7a2e3b8aca6e6f78180f7013575392a3
.. _at a competitor: https://etherscan.io/address/0xd343d2db4306db8cfd917b561fb2b9197e86ff40


Prerequisites
-------------

.. codeblock: sh

   export VIRTUAL_ENV=.virtualenv/cancelot
   mkdir -p $VIRTUAL_ENV
   virtualenv $VIRTUAL_ENV
   source $VIRTUAL_ENV/bin/activate
   pip install -r requirements.txt
   pip install -e . # TODO: make a package on PyPI
   pip install ipython


Usage
-----

Awkward.

The code has been used for a few weeks until its first release with
CPython 3.5. There are no tests.

Sections that are sub-optimal are marked with ``TODO``. Sections
that are down-right horrible are marked with ``FIXME``.

Many functions have side-effects, such as debug messages or warnings.

First run
^^^^^^^^^

``cancelot`` in general is provided as a Python package, with a few
example scripts that use it.

To construct a state for the first time, run:

.. codeblock: sh

   python -u oneshot.py 2>&1 | tee -i -a logs/`date +%s`.log

The result will be a lot of pickle files. Most are saved as "backups"
while the script is running. Save the newest one in the ``pickles``
directory, and remove the rest.

For subsequent runs, use:

.. codeblock: sh

   ./run-oneshot.sh

This will reuse the previous pickle.

Examples
^^^^^^^^

Several "bidding strategy" helpers made it into the repository. There is
little sense in removing them now, since they're not complex anyway, and
it would require some major rewriting of git history, most likely complete
flattening, which I find unacceptable.

Anyway, they are available in ``ipybench.py``. The file is to be run as:

.. codeblock: sh

   ipython -i ipybench.py

By necessity, several lines from IPython history that constitute a minimal
bot are not provided.

This is to guarantee that at least some programming must be done by an
operator wishing to use this, therefore absolving me personally from
being morally responsible for the horrible misfortune they're inevitably
bound to run into.

Revealing the code completely would have also put me at a total disadvantage,
comparing to competing closed-source implementations, whereas now the
handicap is merely severe.


License
-------

Everything in this repository is licensed under GPLv3. See ``LICENSE.txt``.


Trash
-----

First direct tx
^^^^^^^^^^^^^^^

On block 3648565:

https://etherscan.io/tx/0x6e032eed213f1a641af8cdb7fd3770984010a38c04f6c06e393b03dfca30a80d

First reveal?..
^^^^^^^^^^^^^^^

.. codeblock:

   Bid from 0x3c12c57a05780b6e97360392ce18f1ad92fbe0a7 with seal 0x844e77749af1a22536ebbe7fed28588cc4e82302096105f0309db00dd8c79256 added (block 3665634).
   '0x3c12c57a05780b6e97360392ce18f1ad92fbe0a7', '0x00033095b0df8983c66c84b7ff557a5b9b4705a9e22167ae748351d6357ae98b'

First cancel?..
^^^^^^^^^^^^^^^
.. codeblock:

   Bid from 0x3e1f4f4de69e7e2cec0f45153a542d6108ef81bb with seal 0x486e1b9e1e85a60199f98c945ae548c42c51b472b8842181c1d1414a01a4f97c cancd (block 3754090).

Something weird!
^^^^^^^^^^^^^^^^

Possibly a multisig contract doing the bidding?.. Or an index collision?..

.. codeblock:

   WARNING! Key not found in store, skipping bid removal! Tried:
   ('bytes32 not in store', '0x3e35de8f9a0f71c7891245f50a46be4e863244a4', '0x772f91f480a2292645cedee795ffd0f03793e580ba481c16ad23c7b7d0b7f1d6')
   ('bytes32 not in store', '0x3e35de8f9a0f71c7891245f50a46be4e863244a4', '0x0fb37976806ab1a28e0b52bc3b81a240298f3859b560a5b74c08a9fadd21b818')

   WARNING! Key not found in store, skipping bid removal! Tried:
   ('bytes32 not in store', '0x3e35de8f9a0f71c7891245f50a46be4e863244a4', '0x9d2c5cb0cbd9397dbe1b448b1c286f93ee7f51b13c9668bffdd09a22fa3033ba')
   ('bytes32 not in store', '0x3e35de8f9a0f71c7891245f50a46be4e863244a4', '0x0fb37976806ab1a28e0b52bc3b81a240298f3859b560a5b74c08a9fadd21b818')
