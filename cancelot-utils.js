// cancelot geth utilities

loadScript('ensutils.js')

function closestDown(num, arr) {
    if (num < arr[0]) throw 'NumTooLow';

    var closest;
    for (var i = 0; i < arr.length; i++) {
        closest = arr[i];

        var diff = num - arr[i];
        if (diff <= 0) break;
    }

    return closest;
}

function cancelotGP(bidder, seal) {
    var maxGas = 50000; // from 0xdead..'s txs - not tested with own yet
    var reward = 0.005; // 0.5%

    var deed = ethRegistrar.sealedBids(bidder, seal);
    if (deed == '0x0000000000000000000000000000000000000000') throw 'DeedCancelled';

    var maxGP = eth.getBalance(deed) * reward / maxGas;

    // TODO: get from http://ethgasstation.info/hashPowerTable.php
    var gasPricesInShannon = [1, 2, 15, 18, 19, 20, 25, 27, 40, 50]; // 2017-05-29
    // calculate in shannons...
    var shannons = closestDown(web3.fromWei(maxGP, 'shannon'), gasPricesInShannon);

    // ...and convert back to wei
    return web3.toWei(shannons, 'shannon');
}
