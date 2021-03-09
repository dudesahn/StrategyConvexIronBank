import brownie
from brownie import Contract
from brownie import config        

def test_emergency_exit(accounts, token, vault, strategy, strategist, whale, strategyProxy, gaugeIB):
    # Deposit to the vault, confirm that funds are in the gauge
    amount2 = token.balanceOf(whale)
    token.approve(vault.address, amount2, {"from": whale})
    vault.deposit(amount2, {"from": whale})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount2

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit()
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == 0