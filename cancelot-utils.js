// cancelot geth utilities

loadScript('ensutils.js')

function closestDown(num, arr) {
    if (num < arr[0])
        throw 'NumTooLow';
    var closest = arr[0];

    for (var i = 0; i < arr.length; i++) {
        var diff = num - arr[i];
        if (diff <= 0) break;
        closest = arr[i];
    }

    return closest;
}

function cancelotGP(bidder, seal) {
    var minGas = 28177; // see tx 0x2a8411294620fb0b5c5bbf710e7aeddbfb48c778c4a8d56e90a7cb51851016d6
    var maxGas = 49964; // see tx 0xc9f15d91218b3038946c6839495a8cb63eb4d56e98d25acd913cec3ce4921744
    var reward = 0.005; // 0.5%

    var deedaddr = ethRegistrar.sealedBids(bidder, seal);
    if (deedaddr == '0x0000000000000000000000000000000000000000')
        throw 'DeedCancelled';

    var maxGP = eth.getBalance(deedaddr) * reward / maxGas; // float errors galore!

    // TODO: get from http://ethgasstation.info/hashPowerTable.php
    var gasPricesInShannon = [1, 2, 15, 18, 19, 20, 25, 27, 40, 50]; // 2017-05-29
    // calculate in shannons...
    var shannons = closestDown(web3.fromWei(maxGP, 'shannon'), gasPricesInShannon);

    // ...and convert back to wei
    return web3.toWei(shannons, 'shannon');
}

function thrashTx(tx) {
    return eth.resend(tx, tx.gasPrice + 1, testtx.gas);
}
