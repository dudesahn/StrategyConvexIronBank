import brownie
from brownie import Contract
from brownie import config

# test passes as of 21-05-20
def test_sweep(gov, token, vault, dudesahn, strategist, whale, strategy, chain, strategist_ms, rewardsContract):
    # Strategy want token doesn't work
    startingWhale = token.balanceOf(whale)
    token.transfer(strategy.address, 1000e18, {"from": whale})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})