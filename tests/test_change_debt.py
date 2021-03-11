import brownie
from brownie import Contract
from brownie import config

def test_change_debt(gov, token, vault, strategy, strategist, whale, strategyProxy, gaugeIB):
    # Deposit to the vault and harvest
    amount = 100 * ( 10 ** 18)
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    
    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    vault.updateStrategyDebtRatio(strategy, 5000, {"from": gov})
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})

    assert strategyProxy.balanceOf(gaugeIB) == amount / 2
    
    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, 10000, {"from": gov})
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount