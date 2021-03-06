import brownie
from brownie import Contract

def test_change_debt(gov, token, vault, strategy, strategist, whale, strategyProxy, gauge):
    # Deposit to the vault and harvest
    token.approve(vault.address, 10000000000000000000, {"from": whale})
    vault.deposit(10000000000000000000, {"from": whale})
    vault.updateStrategyDebtRatio(strategy.address, 5000000000000000000, {"from": gov})
    strategy.setCrvRouter(0)
    strategy.setOptimal(0)
    strategy.harvest({"from": strategist})

    assert strategyProxy.balanceOf(gauge) == 5000000000000000000

    vault.updateStrategyDebtRatio(strategy.address, 10000000000000000000, {"from": gov})
    strategy.harvest({"from": strategist})
    assert strategyProxy.balanceOf(gauge) == 10000000000000000000

    # In order to pass this tests, you will need to implement prepareReturn.
    # TODO: uncomment the following lines.
    # vault.updateStrategyDebtRatio(strategy.address, 5_000, {"from": gov})
    # assert token.balanceOf(strategy.address) == amount / 2