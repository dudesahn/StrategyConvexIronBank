import brownie
from brownie import Contract
from brownie import config


def test_triggers(gov, vault, strategy, token, strategist, whale):
    # Deposit to the vault and harvest
    amount = 100 * (10 ** 18)
    token.transfer(rando, amount, {"from": whale})
    startingRando = token.balanceOf(rando)
    token.approve(vault.address, amount, {"from": rando})
    vault.deposit(amount, {"from": rando})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.harvest({"from": strategist})
    strategy.harvestTrigger(0)
    strategy.tendTrigger(0)

    # give rando his money back, then he sends back to whale
    vault.withdraw({"from": rando})    
    assert token.balanceOf(rando) >= startingRando
    endingRando = token.balanceOf(rando)
    token.transfer(whale, endingRando, {"from": rando}) 
