import brownie
from brownie import Contract
import pytest
from brownie import config        

def test_emergency_exit(accounts, token, vault, strategy, strategist, amount, whale, strategyProxy, gaugeIB):
    # Deposit to the vault, confirm that funds are in the gauge
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit()
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == 0
    
    # withdrawal to return test state to normal
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) >= amount * 10