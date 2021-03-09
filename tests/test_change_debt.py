import brownie
from brownie import Contract
from brownie import config


def test_change_debt(gov, token, vault, strategy, strategist, whale_change_debt, strategyProxy, gaugeIB, amount):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": whale_change_debt})
    vault.deposit(amount, {"from": whale_change_debt})
    
    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    vault.updateStrategyDebtRatio(strategy, 5000, {"from": gov})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})

    assert strategyProxy.balanceOf(gaugeIB) == amount / 2
    
    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, 10000, {"from": gov})
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount

    # withdrawal to return test state to normal
    vault.withdraw({"from": whale_change_debt})
    assert token.balanceOf(whale_change_debt) != 0