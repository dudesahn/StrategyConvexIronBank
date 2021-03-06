import brownie
from brownie import Contract

def test_emergency_exit(accounts, token, vault, strategy, strategist, amount, whale, strategyProxy, gauge):
    # Deposit to the vault, confirm that funds are in the gauge
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gauge) == amount

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit()
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == 0