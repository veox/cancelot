# Cancelot

A bot to cancel bids in the ENS `.eth` Registrar that were never revealed.

## Overview

The bot is a Python script that connects to a local node over IPC, scans for
placed sealed bids, and tracks which of those haven't been revealed. Once
their expiration timestamp is reached, a call is made to cancel the bid.

## Notes

First direct tx after creation was on block 3648565:

https://etherscan.io/tx/0x6e032eed213f1a641af8cdb7fd3770984010a38c04f6c06e393b03dfca30a80d
