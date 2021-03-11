import brownie
from brownie import Contract
from brownie import config


def test_revoke_strategy_from_vault(token, vault, strategy, gov, strategist, whale, gaugeIB, strategyProxy, voter, chain):
    # Deposit to the vault and harvest
    amount = token.balanceOf(whale)
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == amount

    vault.revokeStrategy(strategy.address, {"from": gov})
    assert strategy.estimatedTotalAssets() == amount
    assert token.balanceOf(vault) == 0

    # This final harvest will collect funds earned from 1 block into vault, as well as amount balance.
    # Unfortunately, there is no way to account for this balance, since you can't check claimable CRV via smart contract.
    strategy.harvest({"from": strategist})

    # So instead of ==, we set this to >= since we know it will have some small amount gained
    assert token.balanceOf(vault) >= amount

    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(2592000)
    chain.mine(1)

    # withdrawal to return test state to normal, we made a profit
    vault.withdraw({"from": whale})
    assert token.balanceOf(whale) >= amount


def test_revoke_strategy_from_strategy(token, vault, strategy, strategist, whale, gov):
    # Deposit to the vault and harvest
    amount = token.balanceOf(whale)
    token.approve(vault.address, amount, {"from": whale})
    vault.deposit(amount, {"from": whale})
    strategy.harvest({"from": strategist})
    assert strategy.estimatedTotalAssets() == amount

    strategy.setEmergencyExit({"from": gov})
    strategy.harvest({"from": strategist})
    assert token.balanceOf(vault) == amount
