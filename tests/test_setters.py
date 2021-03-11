import brownie
from brownie import Contract
from brownie import config

def test_setters(token, vault, strategy, strategist, whale, gaugeIB, strategyProxy, chain, voter):
	# Test all other setter functions, using this address: 0x6b3595068778dd592e39a122f4f5a5cf09c90fe2
	
	
	strategy.setProxy(0x6b3595068778dd592e39a122f4f5a5cf09c90fe2, {"from": gov})
	assert strategy.proxy() = 0x6b3595068778dd592e39a122f4f5a5cf09c90fe2
	
	strategy.updateCheckLiqGauge(0, {"from": gov})
    assert strategy.checkLiqGauge() = 0
	
    strategy.setKeepCRV(2000, {"from": gov})
    assert strategy.keepCRV() > 1000
	
	strategy.setCrvRouter(0, {"from": gov})
	assert strategy.crvRouter != 0
	
	strategy.setVoter(0x6b3595068778dd592e39a122f4f5a5cf09c90fe2, {"from": gov})
	assert strategy.voter() = 0x6b3595068778dd592e39a122f4f5a5cf09c90fe2