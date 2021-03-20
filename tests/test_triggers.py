import brownie
from brownie import Contract
from brownie import config


def test_triggers(gov, token, vault, dudesahn, strategist, whale, strategyProxy, gaugeIB, rando, chain, amount, StrategyCurveIBVoterProxy, live_strategy, vault_balance, strategist_ms):
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
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # harvest to start the timer
    strategy.harvest({"from": dudesahn})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # harvest should trigger false
    tx = strategy.harvestTrigger(0, {"from": dudesahn})
    print("\nShould we harvest? Should be False.", tx)
    
    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)
    
    # harvest should trigger true
    tx = strategy.harvestTrigger(0, {"from": dudesahn})
    print("\nShould we harvest? Should be true.", tx)
    strategy.harvest({"from": dudesahn})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # tend should trigger true,
    tx = strategy.tendTrigger(0, {"from": dudesahn})
    print("\nShould we tend? Should be yes", tx)
    print("\nShould be 0, tendCounter = ", strategy.tendCounter())
    strategy.tend({"from": dudesahn})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # tend should trigger true,
    tx = strategy.tendTrigger(0, {"from": dudesahn})
    print("\nShould we tend? Should be yes", tx)
    print("\nShould be 1, tendCounter = ", strategy.tendCounter())
    strategy.tend({"from": dudesahn})
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
    
    # tend 
    tx = strategy.tendTrigger(0, {"from": dudesahn})
    print("\nShould we tend? Should be yes", tx)
    print("\nShould be 2, tendCounter = ", strategy.tendCounter())
    strategy.tend({"from": dudesahn})
    print("\nShould be 3, tendCounter = ", strategy.tendCounter())
    tx = strategy.tendTrigger(0, {"from": dudesahn})
    print("\nShould we tend? Should be no", tx)

    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)

    # withdraw my money
    vault.withdraw({"from": dudesahn})    
    assert token.balanceOf(dudesahn) > 0