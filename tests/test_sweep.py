import brownie
from brownie import Contract
from brownie import config

def test_sweep(gov, vault, strategy, token, whale):
    # Strategy want token doesn't work
    amount = token.balanceOf(whale)       
    token.transfer(strategy.address, amount, {"from": whale})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})


