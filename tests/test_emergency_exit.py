import brownie
from brownie import Contract
import pytest
from brownie import config        

@pytest.fixture
def whale_emergency(accounts, token ,reserve):
    # Totally in it for the tech
    # Has 5% of tokens (was in the ICO)
    a = accounts[6]
    bal = token.totalSupply() // 20
    token.transfer(a, bal, {"from":reserve})
    yield a


def test_emergency_exit(accounts, token, vault, strategy, strategist, amount, whale_emergency, strategyProxy, gaugeIB):
    # Deposit to the vault, confirm that funds are in the gauge
    token.approve(vault.address, amount, {"from": whale_emergency})
    vault.deposit(amount, {"from": whale_emergency})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount

    # set emergency and exit, then confirm that the strategy has no funds
    strategy.setEmergencyExit()
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == 0