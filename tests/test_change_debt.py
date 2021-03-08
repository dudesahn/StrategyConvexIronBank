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

def test_change_debt(gov, token, vault, strategy, strategist, whale, strategyProxy, gaugeIB, amount):
    # Deposit to the vault and harvest
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    
    # debtRatio is in BPS (aka, max is 10,000, which represents 100%), and is a fraction of the funds that can be in the strategy
    vault.updateStrategyDebtRatio(strategy, 5000, {"from": gov})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})

    assert strategyProxy.balanceOf(gaugeIB) == amount / 2
    
    # set DebtRatio back to 100%
    vault.updateStrategyDebtRatio(strategy, 10000, {"from": gov})
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gaugeIB) == amount

    # In order to pass this tests, you will need to implement prepareReturn.
    # TODO: uncomment the following lines.
    # vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    # assert token.balanceOf(strategy.address) == amount / 2