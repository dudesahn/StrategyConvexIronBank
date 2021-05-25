import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_change_debt(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract, StrategyConvexIronBank, curveVoterProxyStrategy):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    newWhale = token.balanceOf(whale)
    starting_assets = vault.totalAssets()

    # evaluate our current total assets
    startingLive = rewardsContract.balanceOf(strategy)

    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    currentDebt = vault.strategies(strategy)[2]
    vault.updateStrategyDebtRatio(strategy, currentDebt/2, {"from": gov})
    strategy.harvest({"from": dudesahn})

    assert rewardsContract.balanceOf(strategy) < (startingLive)

    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, currentDebt, {"from": gov})
    strategy.harvest({"from": dudesahn})
    assert rewardsContract.balanceOf(strategy) >= startingLive

    # simulate a day of waiting for share price to bump back up
    curveVoterProxyStrategy.harvest({"from": gov})
    chain.sleep(86400)
    chain.mine(1)
    
    # withdraw and confirm we made money
    vault.withdraw({"from": whale})    
    assert token.balanceOf(whale) > startingWhale 
