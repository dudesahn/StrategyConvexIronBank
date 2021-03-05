import brownie
from brownie import Contract

def test_triggers(gov, vault, strategy, token, amount):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)