import brownie
from brownie import Contract
from brownie import config

# TODO: Add tests that show proper migration of the strategy to a newer one
#       Use another copy of the strategy to simulate the migration
#       Show that nothing is lost!

def test_migration(gov, token, vault, dudesahn, strategist, whale, strategyProxy, gaugeIB, rando, chain, amount, StrategyCurveIBVoterProxy, live_strategy, vault_balance, strategist_ms):
    # deploy our new strategy
    new_strategy = dudesahn.deploy(StrategyCurveIBVoterProxy, vault)  
      
    # prepare our live strategy to migrate
    vault.updateStrategyDebtRatio(live_strategy, 0, {"from": strategist_ms})
    live_strategy.harvest({"from": dudesahn})
    
    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(2592000)
    chain.mine(1)    

    # assert that our old strategy is empty
    live_strat_balance = live_strategy.estimatedTotalAssets()
    assert live_strat_balance == 0
    old_gauge_balance = strategyProxy.balanceOf(gaugeIB)
    assert old_gauge_balance == 0
    print("\nLive strategy balance: ", live_strat_balance)
    total_old = vault.totalAssets()
    print("\nTotal Balance to Migrate: ", total_old)
    print("\nProxy gauge balance: ", old_gauge_balance)

    # migrate our old strategy
    vault.migrateStrategy(live_strategy, new_strategy, {"from": strategist_ms})

    # approve on new strategy with proxy
    strategyProxy.approveStrategy(live_strategy.gauge(), new_strategy, {"from": gov})
    vault.updateStrategyDebtRatio(new_strategy, 10000, {"from": strategist_ms})
 
    # Update deposit limit to the vault to $10 million since it's currently maxed out
    vault.setDepositLimit(10000000000000000000000000, {"from": strategist_ms})
    
    # harvest to get funds back in strategy
    new_strategy.harvest({"from": dudesahn})
    new_gauge_balance = strategyProxy.balanceOf(gaugeIB)
    assert new_gauge_balance == total_old
    print("\nNew Proxy gauge balance: ", new_gauge_balance)
    
    startingVault = vault.totalAssets()
    print("\nVault starting assets with new strategy: ", startingVault)
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # test out tend
    new_strategy.tend({"from": dudesahn})
    assert new_strategy.tendCounter() == 1
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # Test out our migrated strategy, confirm we're making a profit
    new_strategy.harvest({"from": dudesahn})
    assert new_strategy.tendCounter() == 0
    vaultAssets_2 = vault.totalAssets()
    assert vaultAssets_2 > startingVault
    print("\nAssets after 1 day harvest: ", vaultAssets_2)
        
    # withdraw my money
    vault.withdraw({"from": dudesahn})    
    assert token.balanceOf(dudesahn) > 0