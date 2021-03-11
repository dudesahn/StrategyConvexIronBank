import brownie
from brownie import Contract
from brownie import config


def test_setters(token, vault, strategy, strategist, whale, gaugeIB, strategyProxy, chain, voter, new_address, gov):
    # Test all other setter functions, using this address: 0x6b3595068778dd592e39a122f4f5a5cf09c90fe2

    strategy.setProxy(new_address, {"from": gov})
    assert strategy.proxy() == new_address

    strategy.updateCheckLiqGauge(0, {"from": gov})
    assert strategy.checkLiqGauge() == 0

    strategy.setKeepCRV(2000, {"from": gov})
    assert strategy.keepCRV() > 1000

    strategy.setCrvRouter(0, {"from": gov})
    assert strategy.crvRouter != 1

    strategy.setVoter(new_address, {"from": gov})
    assert strategy.voter() == new_address
