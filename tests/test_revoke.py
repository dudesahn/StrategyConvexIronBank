import brownie
from brownie import Contract
from brownie import config


def test_revoke_strategy_from_vault(gov, token, vault, dudesahn, strategist, whale, strategyProxy, gaugeIB, rando, chain, amount, StrategyCurveIBVoterProxy, live_strategy, vault_balance, strategist_ms):
    # Update deposit limit to the vault since it's currently maxed out
    vault.setDepositLimit(100000000000000000000000000, {"from": strategist_ms})
    
    # prepare our live strategy to migrate
    vault.updateStrategyDebtRatio(live_strategy, 0, {"from": strategist_ms})
    vault.revokeStrategy(live_strategy.address, {"from": strategist_ms})
    live_strategy.harvest({"from": dudesahn})
    
    # assert that our old strategy is empty
    assert live_strategy.estimatedTotalAssets() == 0

    # deploy our new strategy
    strategy = dudesahn.deploy(StrategyCurveIBVoterProxy, vault)

    # migrate our old strategy
    vault.migrateStrategy(live_strategy, strategy, {"from": strategist_ms})

    # approve on new strategy with proxy
    strategyProxy.approveStrategy(live_strategy.gauge(), strategy, {"from": gov})
    vault.updateStrategyDebtRatio(strategy, 10000, {"from": strategist_ms})
    strategy.harvest({"from": dudesahn})
    startingVault = vault.totalAssets()
    print("\nVault starting assets: ", startingVault)
    
    # assert new_strategy.estimatedTotalAssets() >= holdings
    # assert that our old strategy is empty still
    assert token.balanceOf(strategy) == 0
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # Test out our migrated strategy, confirm we're making a profit
    strategy.harvest({"from": dudesahn})
    assert strategy.tendCounter() == 0
    vaultAssets_2 = vault.totalAssets()
    assert vaultAssets_2 > startingVault
    print("\nAssets after 1 day harvest: ", vaultAssets_2)
    
    ## for default migrations as a part of other tests, just copy all of the text above ##

    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(2592000)
    chain.mine(1)
    strategy.harvest({"from": dudesahn})
    
    assert strategy.estimatedTotalAssets() == vaultAssets_2
    vault.revokeStrategy(strategy.address, {"from": strategist_ms})
    strategy.harvest({"from": dudesahn})
    assert token.balanceOf(vault) >= vaultAssets_2

    # This final harvest will collect funds
    # Unfortunately, there is no way to account for this balance, since you can't check claimable CRV via smart contract.
    strategy.harvest({"from": dudesahn})
    
    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(2592000)
    chain.mine(1)

    # So instead of ==, we set this to >= since we know it will have some small amount gained
    assert token.balanceOf(vault) >= vaultAssets_2

    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(2592000)
    chain.mine(1)

    # withdraw my money
    vault.withdraw({"from": dudesahn})    
    assert token.balanceOf(dudesahn) > 0 