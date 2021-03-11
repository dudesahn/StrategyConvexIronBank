import brownie
from brownie import Contract
from brownie import config


def test_emergency_exit(accounts, token, vault, strategy, strategist, whale, strategyProxy, gaugeIB, rando, chain):
    # Deposit to the vault, confirm that funds are in the gauge
    amount = 100 * (10 ** 18)
    token.transfer(rando, amount, {"from": whale})
    startingRando = token.balanceOf(rando)
    token.approve(vault.address, amount, {"from": rando})
    vault.deposit(amount, {"from": rando})
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit()
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == 0

    # wait for share price to return to normal
    chain.sleep(2592000)
    chain.mine(1)
    
    # give rando his money back, then he sends back to whale
    vault.withdraw({"from": rando})    
    assert token.balanceOf(rando) >= startingRando
    endingRando = token.balanceOf(rando)
    token.transfer(whale, endingRando, {"from": rando})