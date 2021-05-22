import brownie
from brownie import Wei
from pytest import approx


def test_change_debt_with_profit(gov, token, vault, dudesahn, whale, strategy):
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    strategy.harvest({"from": dudesahn})
    prev_params = vault.strategies(strategy).dict()

    vault.updateStrategyDebtRatio(strategy, 25, {"from": gov})
    token.transfer(strategy, Wei("1_000 ether"), {"from": whale})
    strategy.harvest({"from": dudesahn})
    new_params = vault.strategies(strategy).dict()

    assert new_params["totalGain"] > prev_params["totalGain"]
    assert new_params["totalGain"] - prev_params["totalGain"] > Wei("1_000 ether")
    assert new_params["debtRatio"] == 25
    assert new_params["totalLoss"] == prev_params["totalLoss"]
    assert approx(vault.totalAssets() * 0.025, Wei("1 ether")) == strategy.estimatedTotalAssets()
