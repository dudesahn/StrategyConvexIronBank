import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-06-26
def test_remove_from_withdrawal_queue(
    gov, token, vault, whale, strategy, chain, dudesahn, rewardsContract
):
    ## deposit to the vault after approving
    startingWhale = token.balanceOf(whale)
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(10000e18, {"from": whale})
    strategy.harvest({"from": dudesahn})

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    earned_crv = rewardsContract.earned(strategy)/1e18
    print("CRV Earned and waiting to be claimed:", earned_crv)
    assert earned_crv > 0
    strategy.harvest({"from": dudesahn})

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    before = strategy.estimatedTotalAssets()

    # remove strategy from queue, then confirm that our funds haven't gone anywhere
    vault.removeStrategyFromQueue(strategy, {"from": gov})
    after = strategy.estimatedTotalAssets()
    assert before == after

    zero = "0x0000000000000000000000000000000000000000"
    assert vault.withdrawalQueue(2) == zero