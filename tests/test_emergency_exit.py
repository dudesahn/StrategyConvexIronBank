import brownie
from brownie import Contract

def test_emergency_exit(accounts, token, vault, strategy, strategist, amount):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": gov})
    vault.deposit(amount, {"from": gov})
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert token.balanceOf(strategy.address) == amount

    # set emergency and exit
    strategy.setEmergencyExit()
    strategy.harvest({"from": strategist})
    assert token.balanceOf(strategy.address) < amount
