import brownie
from brownie import Contract
import pytest
from brownie import config


@pytest.fixture
def reserve(accounts):
    # this is the gauge contract, holds >99% of pool tokens. use this to seed our whale, as well for calling functions above as gauge
    yield accounts.at("0xF5194c3325202F456c95c1Cf0cA36f8475C1949F", force=True)         

@pytest.fixture
def whale(accounts, token ,reserve):
    # Totally in it for the tech
    # Has 10% of tokens (was in the ICO)
    a = accounts[6]
    bal = token.totalSupply() // 10
    token.transfer(a, bal, {"from":reserve})
    yield a


def test_emergency_exit(accounts, token, vault, strategy, strategist, amount, whale, strategyProxy, gaugeIB):
    # Deposit to the vault, confirm that funds are in the gauge
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit()
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == 0