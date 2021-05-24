import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_emergency_exit(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract, curveVoterProxyStrategy):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    strategy.harvest({"from": dudesahn})

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    earned_crv = rewardsContract.earned(strategy)/1e18
    print("CRV Earned and waiting to be claimed:", earned_crv)
    assert earned_crv > 0

    # confirm that we will claim rewards on withdrawal, set emergency and exit, then confirm that the strategy has no funds
    strategy.setClaimRewards(True, {"from": gov})
    strategy.setEmergencyExit({"from": gov})
    strategy.harvest({"from": dudesahn})
    assert strategy.estimatedTotalAssets() == 0
    assert rewardsContract.balanceOf(strategy) == 0

    # simulate a day of waiting for share price to bump back up
    curveVoterProxyStrategy.harvest({"from": gov})
    chain.sleep(86400)
    chain.mine(1)
    
    # withdraw and confirm we made money
    vault.withdraw({"from": whale})    
    assert token.balanceOf(whale) > startingWhale 
    
def test_emergency_withdraw_method_0(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract, cvxIBDeposit, strat_setup):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    strategy.harvest({"from": dudesahn})

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # set emergency exit so no funds will go back to strategy, and we assume that deposit contract is borked so we go through staking contract
    # here we assume that the swap out to curve pool tokens is borked, so we stay in cvx vault tokens and send to gov
    # we also assume extra rewards are fine, so we will collect them on harvest and withdrawal
    strategy.setHarvestExtras(True, {"from": gov})
    strategy.setClaimRewards(True, {"from": gov})
    strategy.setEmergencyExit({"from": gov})
    
    strategy.withdrawToConvexDepositTokens({"from": dudesahn})
    strategy.harvest({"from": dudesahn})
    assert strategy.estimatedTotalAssets() == 0
    assert rewardsContract.balanceOf(strategy) == 0
    assert cvxIBDeposit.balanceOf(strategy) > 0

    # sweep this from the strategy with gov and wait until we can figure out how to unwrap them
    strategy.sweep(cvxIBDeposit, {"from": gov}) 
    assert cvxIBDeposit.balanceOf(gov) > 0


def test_emergency_withdraw_method_1(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract, cvxIBDeposit, strat_setup):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    strategy.harvest({"from": dudesahn})

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # set emergency exit so no funds will go back to strategy, and we assume that deposit contract is borked so we go through staking contract
    # here we assume that the swap out to curve pool tokens is borked, so we stay in cvx vault tokens and send to gov
    # we also assume extra rewards are borked so we don't want them when harvesting or withdrawing
    strategy.setHarvestExtras(False, {"from": gov})
    strategy.setClaimRewards(False, {"from": gov})
    strategy.setEmergencyExit({"from": gov})
    
    strategy.withdrawToConvexDepositTokens({"from": dudesahn})
    strategy.harvest({"from": dudesahn})
    assert strategy.estimatedTotalAssets() == 0
    assert rewardsContract.balanceOf(strategy) == 0
    assert cvxIBDeposit.balanceOf(strategy) > 0

    strategy.sweep(cvxIBDeposit, {"from": gov})
    assert cvxIBDeposit.balanceOf(gov) > 0