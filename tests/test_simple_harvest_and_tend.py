import brownie
from brownie import Contract
from brownie import config


def test_simple_harvest_and_tend(gov, token, vault, dudesahn, strategist, whale, voter, strategyProxy, gaugeIB, rando, chain, amount, StrategyCurveIBVoterProxy, live_strategy, vault_balance, strategist_ms):
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

    # harvest, store asset amount
    strategy.harvest({"from": dudesahn})
    old_assets_dai = vault.totalAssets()
    assert gaugeIB.balanceOf(voter) == strategyProxy.balanceOf(gaugeIB)
    assert old_assets_dai >= strategyProxy.balanceOf(gaugeIB)
    
    # simulate a day of earnings
    chain.sleep(86400)
    chain.mine(1)
        
    # tend our strategy 
    strategy.tend({"from": dudesahn})
    
    # simulate a month of earnings
    chain.sleep(2592000)
    chain.mine(1)

    # harvest after a month, store new asset amount
    tx = strategy.harvest({"from": dudesahn})
    # tx.call_trace(True)
    new_assets_dai = vault.totalAssets()
    assert new_assets_dai > old_assets_dai

    # Display estimated APR based on the past month
    print("\nEstimated DAI APR: ", "{:.2%}".format(((new_assets_dai - old_assets_dai) * 12) / (old_assets_dai)))

    # wait to allow share price to reach full value (takes 6 hours as of 0.3.2)
    chain.sleep(2592000)
    chain.mine(1)

    # withdraw my money
    vault.withdraw({"from": dudesahn})    
    assert token.balanceOf(dudesahn) > 0 