import brownie
from brownie import Contract
import pytest
from brownie import config


@pytest.fixture
def reserve(accounts):
    # this is the gauge contract, holds >99% of pool tokens. use this to seed our whale_sweep, as well for calling functions above as gauge
    yield accounts.at("0xF5194c3325202F456c95c1Cf0cA36f8475C1949F", force=True)         

@pytest.fixture
def whale_sweep(accounts, token ,reserve):
    # Totally in it for the tech
    # Has 5% of tokens (was in the ICO)
    a = accounts[6]
    bal = token.totalSupply() // 20
    token.transfer(a, bal, {"from":reserve})
    yield a


def test_sweep(gov, vault, strategy, token, amount, whale_sweep):
    # Strategy want token doesn't work
    token.transfer(strategy.address, amount, {"from": whale_sweep})
    assert token.address == strategy.want()
    assert token.balanceOf(strategy) > 0
    with brownie.reverts("!want"):
        strategy.sweep(token, {"from": gov})

    # Vault share token doesn't work
    with brownie.reverts("!shares"):
        strategy.sweep(vault.address, {"from": gov})


