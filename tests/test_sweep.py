import brownie
from brownie import Contract

def test_sweep(gov, vault, strategy, token, amount):
    # Strategy want token doesn't work
    token.transfer(strategy, amount, {"from": whale})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})


