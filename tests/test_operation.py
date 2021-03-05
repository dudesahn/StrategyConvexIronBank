import brownie
# from helpers import showBalances
from brownie import Contract

# **** TEST ALL CONTRACT FUNCTIONS


def test_operation(accounts, token, vault, strategy, strategist, amount):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    assert token.balanceOf(vault.address) == amount

    # set optimal to decide which token to deposit into Curve pool for each harvest (DAI first)
    strategy.setOptimal(0)

    # harvest
    strategy.harvest({"from": strategist})
    assert token.balanceOf(strategy.address) == amount

    # set optimal to USDC
    strategy.setOptimal(1)

    # harvest
    strategy.harvest({"from": strategist})
    assert token.balanceOf(strategy.address) == amount

    # set optimal to USDT
    strategy.setOptimal(2)

    # harvest
    strategy.harvest({"from": strategist})
    assert token.balanceOf(strategy.address) == amount

    # tend()
    strategy.tend()

    # withdrawal
    vault.withdraw({"from": gov})
    assert token.balanceOf(gov) != 0