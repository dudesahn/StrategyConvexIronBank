import brownie
from brownie import Contract
from brownie import config

# TODO: Add tests that show proper migration of the strategy to a newer one
#       Use another copy of the strategy to simulate the migration
#       Show that nothing is lost!

def test_migration(gov, token, vault, dudesahn, strategist, whale, strategyProxy, gaugeIB, rando, chain, amount, StrategyCurveIBVoterProxy, live_strategy, vault_balance, strategist_ms):
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

    # prepare our current strategy to migrate
    vault.updateStrategyDebtRatio(strategy, 0, {"from": strategist_ms})
    vault.revokeStrategy(strategy.address, {"from": strategist_ms})
    strategy.harvest({"from": dudesahn})

    # migrate to a new strategy, but can effectively re-deploy existing strategy to serve as second strategy
    new_strategy = dudesahn.deploy(StrategyCurveIBVoterProxy, vault)
    strategyProxy.approveStrategy(live_strategy.gauge(), new_strategy, {"from": gov})
    vault.migrateStrategy(strategy, new_strategy, {"from": strategist_ms})
    vault.updateStrategyDebtRatio(new_strategy, 10000, {"from": strategist_ms})
    assert strategy.estimatedTotalAssets() == 0
    new_strategy.harvest({"from": dudesahn})
    assert new_strategy.estimatedTotalAssets() >= vaultAssets_2
    
    # withdraw my money
    vault.withdraw({"from": dudesahn})    
    assert token.balanceOf(dudesahn) > 0