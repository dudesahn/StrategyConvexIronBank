import brownie
from brownie import Wei
from pytest import approx


def test_change_debt_with_profit(gov, token, vault, dudesahn, whale, strategy, curveVoterProxyStrategy):
    token.approve(vault, 2 ** 256 - 1, {"from": whale})
    vault.deposit(100000e18, {"from": whale})
    strategy.harvest({"from": dudesahn})
    prev_params = vault.strategies(strategy).dict()

    currentDebt = vault.strategies(strategy)[2]
    vault.updateStrategyDebtRatio(strategy, currentDebt/2, {"from": gov})
    token.transfer(strategy, Wei("1_000 ether"), {"from": whale})
    
    # need to harvest our other strategy first so we don't pay all of the management fee from this strategy
    curveVoterProxyStrategy.harvest({"from": gov})
    strategy.harvest({"from": dudesahn})
    new_params = vault.strategies(strategy).dict()
    
    assert new_params["totalGain"] > prev_params["totalGain"]
    assert new_params["totalGain"] - prev_params["totalGain"] > Wei("1_000 ether")
    assert new_params["debtRatio"] == currentDebt/2
    assert new_params["totalLoss"] == prev_params["totalLoss"]
    assert approx(vault.totalAssets() * 0.150, Wei("1 ether")) == strategy.estimatedTotalAssets()
