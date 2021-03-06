import brownie
from brownie import Contract

def test_change_debt(gov, token, vault, strategy, strategist, amount):
    # Deposit to the vault and harvest
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})

    assert token.balanceOf(strategy.address) == amount / 2

    vault.updateStrategyDebtRatio(strategy.address, 10_000, {"from": gov})
    strategy.harvest({"from": strategist})
    assert token.balanceOf(strategy.address) == amount

    # In order to pass this tests, you will need to implement prepareReturn.
    # TODO: uncomment the following lines.
    # vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    # assert token.balanceOf(strategy.address) == amount / 2


