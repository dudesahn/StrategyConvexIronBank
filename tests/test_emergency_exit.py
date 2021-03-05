import brownie
from brownie import Contract

def test_emergency_exit(accounts, token, vault, strategy, strategist, amount):
    # Deposit to the vault
    token.approve(vault.address, amount, {"from": accounts[0]})
    vault.deposit(amount, {"from": accounts[0]})
    strategy.setOptimal(0, {"from": gov})
    strategy.harvest({"from": gov})
    assert token.balanceOf(strategy.address) == amount

    # set emergency and exit
    strategy.setEmergencyExit()
    strategy.harvest({"from": gov})
    assert token.balanceOf(strategy.address) < amount
