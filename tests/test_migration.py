import brownie
from brownie import Contract
from brownie import config

# TODO: Add tests that show proper migration of the strategy to a newer one
#       Use another copy of the strategy to simulate the migration
#       Show that nothing is lost!


def test_migration(token, vault, strategy, strategist, gov, whale, StrategyCurveIBVoterProxy, rando, chain):
    # Deposit to the vault and harvest
    amount = 100 * (10 ** 18)
    token.transfer(rando, amount, {"from": whale})
    startingRando = token.balanceOf(rando)
    token.approve(vault.address, amount, {"from": rando})
    vault.deposit(amount, {"from": rando})
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == amount

    # migrate to a new strategy, but can effectively re-deploy existing strategy to serve as second strategy
    new_strategy = strategist.deploy(StrategyCurveIBVoterProxy, vault)
    strategy.migrate(new_strategy.address, {"from": gov})
    assert new_strategy.estimatedTotalAssets() == amount
    assert strategy.estimatedTotalAssets() == 0
    
    # give rando his money back, then he sends back to whale
    vault.withdraw({"from": rando})    
    assert token.balanceOf(rando) >= startingRando
    endingRando = token.balanceOf(rando)
    token.transfer(whale, endingRando, {"from": rando})