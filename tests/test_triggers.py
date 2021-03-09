import brownie
from brownie import Contract
from brownie import config


def test_triggers(gov, vault, strategy, token, amount, strategist, whale_triggers):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": whale_triggers})
    vault.deposit(amount, {"from": whale_triggers})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)
    
    # withdrawal to return test state to normal
    vault.withdraw({"from": whale_triggers})
    assert token.balanceOf(whale_triggers) != 0