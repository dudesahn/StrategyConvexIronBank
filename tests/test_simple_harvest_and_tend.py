import brownie
from brownie import Contract
from brownie import config


def test_simple_harvest_and_tend(gov, token, vault, dudesahn, strategist, whale, strategy, voter, gaugeIB, chain, strategist_ms):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(1000e18, {"from": whale})
    newWhale = token.balanceOf(whale)
    
    # harvest, store asset amount
    strategy.harvest({"from": gov})
    old_assets_dai = strategy.estimatedTotalAssets()
    assert old_assets_dai > 0
    assert token.balanceOf(strategy) == 0
        
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # harvest after a day, store new asset amount
    strategy.harvest({"from": gov})
    # tx.call_trace(True)
    new_assets_dai = strategy.estimatedTotalAssets()
    assert new_assets_dai > old_assets_dai

    # Display estimated APR based on the past day
    print("\nEstimated DAI APR: ", "{:.2%}".format(((new_assets_dai - old_assets_dai) * 365) / (old_assets_dai)))
    
    # simulate a day of waiting for share price to bump back up
    chain.sleep(86400)
    chain.mine(1)
    
    # withdraw and confirm we made money
    vault.withdraw({"from": whale})    
    assert token.balanceOf(whale) > startingWhale 