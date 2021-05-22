import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_change_debt(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract, StrategyConvexIronBank):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    newWhale = token.balanceOf(whale)
    starting_assets = vault.totalAssets()

    # evaluate our current total assets
    startingLive = rewardsContract.balanceOf(strategy)

    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    vault.updateStrategyDebtRatio(strategy, 25, {"from": gov})
    strategy.harvest({"from": dudesahn})

    assert rewardsContract.balanceOf(strategy) < ( startingLive / 1.99 )

    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, 50, {"from": gov})
    strategy.harvest({"from": dudesahn})
    assert rewardsContract.balanceOf(strategy) >= startingLive

    # wait for share price to return to normal
    chain.sleep(86400)
    chain.mine(1)
    
    # withdraw and confirm we made money
    vault.withdraw({"from": whale})    
    assert token.balanceOf(whale) > startingWhale 
