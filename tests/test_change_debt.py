import brownie
from brownie import Contract
from brownie import config

def test_change_debt(gov, token, vault, strategy, strategist, whale, strategyProxy, gaugeIB):
    # Deposit to the vault and harvest
    amount1 = token.balanceOf(whale) / 10
    token.approve(vault.address, amount1, {"from": whale})
    vault.deposit(amount1, {"from": whale})
    
    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    vault.updateStrategyDebtRatio(strategy, 5000, {"from": gov})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})

    assert strategyProxy.balanceOf(gaugeIB) == amount1 / 2
    
    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, 10000, {"from": gov})
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount1