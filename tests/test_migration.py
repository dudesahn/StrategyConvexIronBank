import brownie
from brownie import Contract
import pytest
from brownie import config
    
# TODO: Add tests that show proper migration of the strategy to a newer one
#       Use another copy of the strategy to simulate the migration
#       Show that nothing is lost!


def test_migration(token, vault, strategy, amount, strategist, gov, whale, StrategyCurveIBVoterProxy):
    # Put some funds into current strategy
    amount = token.balanceOf(whale) * 0.1    
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == amount

    # migrate to a new strategy, but can effectively re-deploy existing strategy to serve as second strategy
    new_strategy = strategist.deploy(StrategyCurveIBVoterProxy, vault)
    strategy.migrate(new_strategy.address, {"from": gov})
    assert new_strategy.estimatedTotalAssets() == amount
    assert strategy.estimatedTotalAssets() == 0
    
    # withdrawal to return test state to normal
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) >= amount * 10
    
    
