// cancelot geth utilities

loadScript('ensutils.js')

function closestDown(num, arr) {
    if (num < arr[0])
        throw 'NumTooLow';
    var closest = arr[0];

    for (var i = 0; i < arr.length; i++) {
        if (num - arr[i] <= 0) break;
        closest = arr[i];
    }

    return closest;
}

// TODO: get from http://ethgasstation.info/json/price.json
var gasPricesInShannon = [1, 4, 18, 23, 27, 46]; // 2017-06-24

function cancelotGP(bidder, seal) {
    var minGas = 28177; // see tx 0x2a8411294620fb0b5c5bbf710e7aeddbfb48c778c4a8d56e90a7cb51851016d6
    var maxGas = 49964; // see tx 0xc9f15d91218b3038946c6839495a8cb63eb4d56e98d25acd913cec3ce4921744
    var reward = 0.005; // 0.5%

    var deedaddr = ethRegistrar.sealedBids(bidder, seal);
    if (deedaddr == '0x0000000000000000000000000000000000000000')
        throw 'DeedCancelled';

    var maxGP = eth.getBalance(deedaddr) * reward / maxGas; // float errors galore!

    // calculate in shannons...
    var shannons = closestDown(web3.fromWei(maxGP, 'shannon'), gasPricesInShannon);

    // ...and convert back to wei
    return [web3.toWei(shannons, 'shannon'), web3.toWei(maxGP, 'wei')];
}

function thrashTx(tx) {
    return eth.resend(tx, tx.gasPrice + 1, testtx.gas);
}

var CancelotAddress = '0xC9C7Db3C7a2e3b8AcA6E6F78180F7013575392a3';
var CancelotABI = [{"constant":false,"inputs":[],"name":"terminate","outputs":[],"payable":false,"type":"function"},{"constant":false,"inputs":[],"name":"withdraw","outputs":[],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"bidder","type":"address"},{"name":"seal","type":"bytes32"}],"name":"sweep","outputs":[],"payable":false,"type":"function"},{"constant":true,"inputs":[],"name":"owner","outputs":[{"name":"","type":"address"}],"payable":false,"type":"function"},{"constant":false,"inputs":[{"name":"bidder","type":"address"},{"name":"seal","type":"bytes32"}],"name":"cancel","outputs":[],"payable":false,"type":"function"},{"inputs":[{"name":"_owner","type":"address"},{"name":"_registrar","type":"address"}],"payable":false,"type":"constructor"},{"payable":true,"type":"fallback"}]
var Cancelot = eth.contract(CancelotABI).at(CancelotAddress);
