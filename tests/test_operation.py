import brownie
# from helpers import showBalances
from brownie import Contract

# **** TEST ALL CONTRACT FUNCTIONS


def test_operation(accounts, token, vault, strategy, strategist, amount, whale):
    # Deposit to the vault
    token.approve(vault, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    assert token.balanceOf(vault) == amount

    # set optimal to decide which token to deposit into Curve pool for each harvest (DAI first)
    strategy.setOptimal(0)

    # harvest
    strategy.harvest({"from": strategist})
    assert token.balanceOf(strategy.address) == amount

#     set optimal to USDC
#     strategy.setOptimal(1)
# 
#     harvest
#     strategy.harvest({"from": strategist})
#     assert token.balanceOf(strategy.address) == amount
# 
#     set optimal to USDT
#     strategy.setOptimal(2)
# 
#     harvest
#     strategy.harvest({"from": strategist})
#     assert token.balanceOf(strategy.address) == amount

    # tend()
    strategy.tend()

    # withdrawal
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) != 0